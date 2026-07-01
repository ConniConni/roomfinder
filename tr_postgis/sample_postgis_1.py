# 東京タワー付近（139.745, 35.658）から半径1000m以内のIDを探す

# psycopg2でDB接続(接続情報は安全に渡す)
# クエリ実行
# 600万行あるので
# ①BboxとST_Expand()でインデックスを使って絞り込み
# ②その後ST_DWithin()でメートル単位で正確に判定
# ファイル書き込み(extraction_point.csv)
# curからforループで取り出し、csvモジュールのwrite()メソッドを使用

import csv
import os
import psycopg2
from dotenv import load_dotenv

# 基準点:東京タワー
TARGET_POINT = (35.658, 139.745)

# .envファイル読み込み接続情報を取得
load_dotenv()

dbname = os.getenv("POSTGRES_DB")
user = os.getenv("POSTGRES_USER")
password = os.getenv("POSTGRES_PASSWORD")
port = os.getenv("POSTGRES_PORT")

# psycopg2の接続処理に使用する引数の形にまとめる
db_config = {
    "host": "localhost",
    "port": port,
    "database": dbname,
    "user": user,
    "password": password,
}

# 実行するSQL
sql = """
    SELECT id, ST_AsText(geom) AS geom
    FROM training_data
    WHERE geom && ST_Expand(ST_GeomFromText(%(point_wkt)s, 4326), 0.015)
    AND ST_DWithin(
        geom::geography,
        ST_GeogFromText(%(point_wkt)s),
        1000
    )
    ORDER BY id;
"""

# SQL実行の際に渡す引数
parse = f"POINT({TARGET_POINT[1]} {TARGET_POINT[0]})"


# finally句で明示的に接続を閉じるために定義
conn = None

try:
    # 正常終了時は自動でcommit
    # エラー発生時は自動でrollback（その後except句の処理）
    with psycopg2.connect(**db_config) as conn:
        print("DB接続")
        # with句を抜けたら自動でカーソルを閉じる
        with conn.cursor() as cur:
            cur.execute(sql, {"point_wkt": parse})
            rows = cur.fetchall()
            total_rows = len(rows)

        header = ["id", "geom"]

        with open("extraction_point.csv", mode="w", encoding="utf-8") as f:
            write = csv.writer(f)

            # ヘッダー書き込み
            write.writerow(header)
            # 取得したidとgeomを書き込み
            write.writerows(rows)
            print(f"{total_rows}件 のデータをファイルに書き込みました。")


except psycopg2.Error as e:
    print(f"DBエラーが発生しました。:{e}")

finally:
    if conn:
        conn.close()
    print("DB切断")
