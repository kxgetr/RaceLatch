def scenario(checkpoint):
    state={'total':0}
    def worker():
        checkpoint('before read')
        value=state['total']
        checkpoint('before write')
        state['total']=value+1
    def check():
        assert state['total']==2, f"lost update: total={state['total']}"
    return {'A':worker,'B':worker},check
