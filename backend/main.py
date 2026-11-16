from fastapi import FastAPI

app = FastAPI(title="RetenSight")


@app.get("/api/health")
def health():
    return {"status": "ok"}
