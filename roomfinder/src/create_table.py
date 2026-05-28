import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

port_num = os.getenv("POSTGRES_PORT")
database_name = os.getenv("POSTGRES_DB")
user_name = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")


db_config = {
    "host": "localhost",
    "port": port_num,
    "database": database_name,
    "user": user_name,
    "password": password,
}


def db_connect(**config):
    return psycopg2.connect(**config)


if __name__ == "__main__":

    conn = db_connect(**db_config)
    if conn:
        print(f"DB: {database_name} に接続しました。")
    else:
        print("DB接続に失敗しました。")

    if conn:
        conn.close()
        print(f"DB: {database_name} を接断しました。")
