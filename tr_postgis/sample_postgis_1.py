# 東京タワー付近（139.745, 35.658）から半径1000m以内のIDを探す

# psycopg2でDB接続(接続情報は安全に渡す)
# クエリ実行
# 600万行あるので
# ①BboxとST_Expand()でインデックスを使って絞り込み
# ②その後ST_DWithin()でメートル単位で正確に判定
# ファイル書き込み(extraction_point.csv)
# curからforループで取り出し、csvモジュールのwrite()メソッドを使用

import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

dbname = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
port = os.getenv("POSTGRES_PORT")

db_config = {
    "host": "localhost",
    "port": port,
    "database": dbname,
    "user": user,
    "password": password,
}

# finally句で明示的に接続を閉じるために定義
conn = None

try:
    # 正常終了時は自動でcommit
    # エラー発生時は自動でrollback（その後except句の処理）
    with psycopg2.connect(**db_config) as conn:
        print("DB接続")
        # with句を抜けたら自動でカーソルを閉じる
        with conn.cursor() as cur:
            pass

except psycopg2.Error as e:
    print(f"DBエラーが発生しました。:{e}")

finally:
    if conn:
        conn.close()
    print("DB切断")
