from fastapi import FastAPI
from .auth import router
app=FastAPI(title="GRTAlgo")
app.include_router(router)
@app.get("/health")
def health():
    return {"status":"ok","trading_mode":"paper","execution_enabled":False}
