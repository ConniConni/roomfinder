import os

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv


def get_db_config_property():
    """envファイルを読み込み、DB接続情報を辞書型で返す"""
    load_dotenv()

    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    config = {
        "host": "localhost",
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }

    return config


def db_connect(**config):
    return psycopg2.connect(**config)


def execute_insert_query(cur, table, query_body, params=None):
    """
    引数で受け取ったsqlを実行する
    Args:
        cur: カーソル
        table: データを挿入するテーブル名
        sql: 実行するsql文
        params: sqlに埋め込むパラメータ デフォルトはNone
    """

    query = sql.SQL("TRUNCATE TABLE {} CASCADE;").format(sql.Identifier(table))
    cur.execute(query)
    print(f"EXECUTE SQL: {cur.mogrify(query).decode('utf-8')}")

    cur.execute(query_body, params)
    print(f"EXECUTE SQL: {cur.mogrify(query_body, params).decode('utf-8')}")


if __name__ == "__main__":
    conn = None
    db_config = get_db_config_property()

    try:
        with db_connect(**db_config) as conn:
            with conn.cursor() as cur:
                # データ読み込み
                # データクレンジング
                # INSERT文組み立て
                query = "INSERT INTO railway_stations (name, line_name, geom) VALUES ('天神', '貫線', ST_GeomFromText('POINT(130.39863 33.59126)', 4326));"
                execute_insert_query(cur, "railway_stations", query)
                print("○件のデータを登録しました。")

    except psycopg2.OperationalError as e:
        print(f"データベース接続エラー: {e}")
    except psycopg2.IntegrityError as e:
        print(f"データ整合性エラー（重複など）: {e}")
    except psycopg2.Error as e:
        print(f"psycopg2の一般的なエラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")
