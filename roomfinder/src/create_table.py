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

    conn = None
    try:
        with db_connect(**db_config) as conn:
            print(f"DB: {database_name} に接続しました。")
            with conn.cursor() as cur:
                pass

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
