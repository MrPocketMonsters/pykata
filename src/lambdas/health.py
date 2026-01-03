from mangum import Mangum
from fastapi import FastAPI

app = FastAPI()


@app.get("/health")
def health_check():
    return {"status": "ok"}


handler = Mangum(app)
