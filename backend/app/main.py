from fastapi import FastAPI

app = FastAPI(title="Madcamp Week4 API")


@app.get("/")
def read_root() -> dict:
    return {"message": "FastAPI is running"}
