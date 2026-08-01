from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()


@app.get("/")
async def get_search_result():
    return {"message": "Hello World!"}
