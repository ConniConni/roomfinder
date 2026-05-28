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


create_table_railway = """
DROP TABLE IF EXISTS railway_stations;
CREATE TABLE railway_stations (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    line_name TEXT NOT NULL,
    geom Geometry(Point, 4326) NOT NULL
);
CREATE INDEX idx_railway_stations_geom ON railway_stations USING GiST (geom);
"""


def db_connect(**config):
    return psycopg2.connect(**config)


def crate_table(cur, query):
    """
    引数で受け取ったクエリを実行し、テーブルを生成する
    Args:
        cur: カーソル
        query: CREATE TABLE文が書かれた文字列
    """

    cur.execute(query)
    execute_query = cur.mogrify(query).decode("utf-8")
    print(f"EXECUTE SQL: {execute_query}")


if __name__ == "__main__":

    conn = None
    try:
        with db_connect(**db_config) as conn:
            print(f"DB: {database_name} に接続しました。")
            with conn.cursor() as cur:
                crate_table(cur, create_table_railway)

    except psycopg2.OperationalError as e:
        print(f"データベース接続エラー: {e}")
    except psycopg2.IntegrityError as e:
        print(f"データ整合性エラー（重複など）: {e}")
    except psycopg2.Error as e:
        print(f"psycopg2の一般的なエラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")

    finally:
        if conn:
            conn.close()
            print(f"DB: {database_name} を接断しました。")
        else:
            print(f"DB接続に失敗しました。")
