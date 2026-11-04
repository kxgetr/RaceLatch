import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
CLI = HERE / 'racelatch.py'

def run(*args, expected=0):
    result = subprocess.run([sys.executable, str(CLI), *map(str, args)],
                            capture_output=True, text=True, timeout=30)
    assert result.returncode == expected, (args, result.stdout, result.stderr)
    return result.stdout

with tempfile.TemporaryDirectory() as folder:
    original = Path.cwd()
    os.chdir(folder)
    try:
        output=json.loads(run(HERE/'counter.py',expected=1))
        assert output['failure']=='lost update: total=1'
        assert json.loads(run(HERE/'counter.py','--replay','race.json',expected=1))['reproduced']
        assert not json.loads(run(HERE/'counter.py','--budget','1',expected=2))['complete']
    finally:
        os.chdir(original)
print("PASS: RaceLatch")
