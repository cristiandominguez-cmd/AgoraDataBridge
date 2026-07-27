from fastapi import FastAPI

app = FastAPI(title="Agora Data Bridge")


@app.get("/")
def root():
    return {
        "application": "Agora Data Bridge",
        "status": "running"
    }
