# 東京タワー付近（139.745, 35.658）から半径1000m以内のIDを探す

# psycopg2でDB接続(接続情報は安全に渡す)
# クエリ実行
# 600万行あるので
# ①BboxとST_Expand()でインデックスを使って絞り込み
# ②その後ST_DWithin()でメートル単位で正確に判定
# ファイル書き込み(extraction_point.csv)
# curからforループで取り出し、csvモジュールのwrite()メソッドを使用

import csv
import logging
import psycopg2

import config

# --- 定数 ---
# 基準点:東京タワー
TARGET_POINT = (35.658, 139.745)
CSV_FILE_NAME = "extraction_point.csv"


# --- ロギング設定 ---
config.setup_logging()
logger = logging.getLogger(__name__)


# --- 関数定義 ---
def connect_db(db_config):
    """
    DBへの接続を確立する

    args:
        db_config (dict): DB接続情報

    return:
        conn (object): 接続オブジェクト
    """

    conn = psycopg2.connect(**db_config)

    if conn:
        logger.info("DB接続")
    return conn


def fetch_data_from_db(conn, param):
    """
    クエリを実行してデータを取得する

    args:
        conn (object): 接続オブジェクト
        params (string): SQLのパラメータ

    return:
        rows (list): クエリの実行結果
    """
    # 取得したデータの保存先を定義
    rows = []

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

    with conn.cursor() as cur:
        cur.execute(sql, {"point_wkt": param})
        log_msg_sql = cur.mogrify(sql, {"point_wkt": param}).decode("utf-8")
        logger.debug(log_msg_sql)
        rows = cur.fetchall()

    return rows


def save_to_csv(file_name, rows):
    """
    CSVファイルにリストのデータを書き込む

    args:
        file_name (string): ファイル名
        rows (list): 書き込み対象のリスト
    """

    if not rows:
        logger.info("取得結果が0件のためCSVファイルの出力をスキップ")
        return

    header = ["id", "geom"]

    with open(file_name, mode="w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)

        # ヘッダー書き込み
        write.writerow(header)
        # 取得したidとgeomを書き込み
        write.writerows(rows)
        logger.info(f"{len(rows)}件 のデータをファイルに書き込みました。")


# --- メイン処理 ---
def main():
    # DB接続情報を取得
    db_config = config.get_db_config()
    # SQL実行の際に渡す引数
    point_wkt = f"POINT({TARGET_POINT[1]} {TARGET_POINT[0]})"

    # 正常終了時は自動でcommit
    # エラー発生時は自動でrollback（その後except句の処理）
    # with句を抜けたら自動でカーソルを閉じる
    try:
        conn = None  # 初期化
        # DB接続
        with connect_db(db_config) as conn:
            # データ取得
            fetch_rows = fetch_data_from_db(conn, point_wkt)

        # 取得したデータをCSVに出力
        save_to_csv(CSV_FILE_NAME, fetch_rows)

    except psycopg2.OperationalError as e:
        logger.error(f"【DB接続エラー】設定を見直してください。:{e}")

    except psycopg2.ProgrammingError as e:
        logger.error(f"【SQL実行エラー】クエリの内容を確認してください。:{e}")

    except psycopg2.Error as e:
        logger.error(f"【その他DBエラー】:{e}")

    finally:
        if conn:
            conn.close()
            logger.info("DB切断")


if __name__ == "__main__":
    main()
