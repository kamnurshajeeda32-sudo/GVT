from fastapi import FastAPI

app = FastAPI(title='GRTAlgo')

@app.get('/health')
def health():
    return {'status': 'ok', 'trading_mode': 'paper', 'execution_enabled': False}
