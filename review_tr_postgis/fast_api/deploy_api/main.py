import os
import psycopg2
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

env_dir = Path(__file__).parent.parent.parent.parent / ".env"


class Data(BaseModel):
    x: float
    y: float


def db_config(env_path):
    load_dotenv(env_path)

    config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    return config


app = FastAPI()


@app.get("/")
async def index():

    return {"message": "Hello Deta!"}


@app.get("/result")
async def get_search_info():
    try:
        config = db_config(env_dir)
        with psycopg2.connect(**config) as conn:
            pass
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1, 'test', 'bakery', ST_AsText(ST_GeomFromText('POINT(139.48 35.92)', 4326));"
                )
                rows = cur.fetchall()
        return {"result": rows[0]}
    except Exception as e:
        return {"status": "error", "error_type": str(type(e)), "message": str(e)}


@app.post("/")
async def calc(
    data: Data,
):
    result = data.x * data.y
    return {"result": result}
