"""Explore deterministic schedules for instrumented Python threads."""
import argparse
import importlib.util
import json
import sys
import threading
from pathlib import Path

def run(factory, order):
    condition = threading.Condition()
    waiting, errors = {}, []
    finished = set()
    stop = False
    permit = None
    trace = []

    class Cancelled(BaseException):
        pass

    def checkpoint(label):
        nonlocal permit
        name = threading.current_thread().name
        with condition:
            waiting[name] = label
            condition.notify_all()
            condition.wait_for(lambda: stop or permit == name)
            if stop:
                raise Cancelled()
            permit = None
            del waiting[name]

    workers, check = factory(checkpoint)
    def execute(name, job):
        try:
            checkpoint("start")
            job()
        except Cancelled:
            pass
        except BaseException as exc:
            errors.append(exc)
        finally:
            with condition:
                finished.add(name)
                condition.notify_all()

    threads = [threading.Thread(name=name, target=execute, args=(name,job), daemon=True)
               for name,job in workers.items()]
    for thread in threads:
        thread.start()
    def settled():
        return permit is None and len(waiting) + len(finished) == len(workers)
    try:
        with condition:
            if not condition.wait_for(settled, 5):
                raise ValueError("initial checkpoint timeout")
            for name in order:
                if name not in waiting:
                    raise ValueError("schedule no longer matches scenario")
                trace.append([name,waiting[name]])
                permit = name
                condition.notify_all()
                if not condition.wait_for(settled, 5):
                    raise ValueError("worker blocked outside checkpoint")
                if errors:
                    raise errors[0]
            if not waiting:
                check()
            return sorted(waiting),trace,None
    except AssertionError as err:
        return [],trace,str(err) or 'AssertionError'
    finally:
        with condition:
            stop = True
            condition.notify_all()
        for thread in threads:
            thread.join(timeout=1)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('scenario',type=Path)
    p.add_argument('--budget',type=int,default=2000)
    p.add_argument('--depth',type=int,default=40)
    p.add_argument('--out',type=Path,default=Path('race.json'))
    p.add_argument('--replay',type=Path)
    a=p.parse_args()
    path=a.scenario.resolve()
    sys.path.insert(0,str(path.parent))
    spec=importlib.util.spec_from_file_location('race_scenario',path)
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    if a.replay:
        saved=json.loads(a.replay.read_text())
        pending,trace,error=run(module.scenario,saved['order'])
        hit=error is not None and error==saved['failure'] and trace==saved['trace']
        print(json.dumps(dict(reproduced=hit,failure=error,trace=trace)))
        return 1 if hit else 2
    stack=[[]]
    explored=0
    clipped=False
    while stack and explored<a.budget:
        order=stack.pop()
        choices,trace,error=run(module.scenario,order)
        explored+=1
        if error is not None:
            record=dict(order=order,trace=trace,failure=error)
            a.out.write_text(json.dumps(record,indent=2))
            print(json.dumps(record))
            return 1
        if len(order)<a.depth: stack.extend(order+[name] for name in reversed(choices))
        elif choices: clipped=True
    print(json.dumps(dict(explored=explored,complete=not stack and not clipped)))
    return 2 if stack or clipped else 0
if __name__=='__main__': sys.exit(main())
