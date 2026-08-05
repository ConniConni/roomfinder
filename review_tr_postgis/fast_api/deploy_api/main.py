import logging
import os
import psycopg2
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

# --- 定数 ---
TARGET_POINTS = [
    (35.92, 139.48, "川越A"),
    (34.68, 135.99, "奈良B"),
    (34.68, 135.99, "奈良C"),
    (35.41, 136.76, "岐阜D"),
    (43.30, 142.42, "岐阜E"),
    (33.32, 130.94, "日田F"),
]
SEARCH_RADIUS_M = 1000
MAX_SEARCH_RADIUS_M = 10000
MAX_WORKERS = 3
MAX_LAT = 145.6
MIN_LAT = 20.4
MAX_LNG = 154.0
MIN_LNG = 122.9

# --- 変数 ---
# ログファイル格納先
log_dir = Path(__file__).parent / "logs"
# 単位:度でのざっくりとした絞り込み用の係数
search_radius_padding_factor = SEARCH_RADIUS_M / 111000 * 1.5
# .envファイルのパス
env_dir = Path(__file__).parent.parent.parent.parent / ".env"


class Data(BaseModel):
    x: float
    y: float


class ParallelDataFetcher:
    """
    DBから対象のデータを取得し、
    取得データのリスト、処理の成功フラグ、および基準となると地点名
    を一元管理して返す

    Attributes:
        db_config (dict): DB接続情報
        target_point (tuple): 緯度, 経度
        search_radius (int): 検索半径
        padding_factor (float): 検索距離(度)
        max_workers (int): スレッド数
        conn : DB接続オブジェクト 初期値 None

    """

    def __init__(self, db_config, target_point, search_radius, padding_factor):
        """インスタンス変数を初期化"""
        self.db_config = db_config
        self.target_point = target_point
        self.search_radius = search_radius
        self.padding_factor = padding_factor
        self.conn = None

    def connect(self):
        """
        DB接続を確保し、connを返す
        Return:
            conn :DB接続オブジェクト
        """
        self.conn = psycopg2.connect(**self.db_config)
        logger.info("DB接続成功")

        return self.conn

    def fetch_list(self):
        """
        SQLを実行し、対象の地点を取得し、リストで返却する
        Return:
            result (list): 取得したリスト
        """

        sql_body = """
            SELECT
                id, name, category, ST_AsText(geom)
            FROM stores
            WHERE geom && ST_Expand(ST_GeomFromText(%(point_wkt)s, 4326), %(deg_factor)s)
            AND ST_DWithin(ST_GeomFromText(%(point_wkt)s, 4326)::geography, geom::geography, %(dist)s)
            ;
        """
        # パラメータ組み立て
        lat, lng = self.target_point
        point_wkt = f"POINT({lng} {lat})"

        with self.conn.cursor() as cur:
            cur.execute(
                sql_body,
                {
                    "point_wkt": point_wkt,
                    "deg_factor": self.padding_factor,
                    "dist": self.search_radius,
                },
            )
            log_msg_sql = cur.mogrify(
                sql_body,
                {
                    "point_wkt": point_wkt,
                    "deg_factor": self.padding_factor,
                    "dist": self.search_radius,
                },
            ).decode("utf-8")
            logger.debug(log_msg_sql)
            fetch_date = cur.fetchall()

            return fetch_date

    def run(self):
        """
        実行メソッド
        """
        is_success = False
        fetch_rows = []
        try:
            with self.connect() as conn:
                fetch_rows = self.fetch_list()
            is_success = True

        except psycopg2.OperationalError as e:
            logger.error(f"【DB接続エラー】設定を見直してください。:{e}")

        except psycopg2.ProgrammingError as e:
            logger.error(f"【SQL実行エラー】クエリの内容を確認してください。:{e}")

        except psycopg2.Error as e:
            logger.error(f"【その他DBエラー】:{e}")

        except Exception as e:
            logger.error(f"【予期せぬエラー】:{e}")
        finally:
            if self.conn:
                self.conn.close()
                logger.info("DB切断")

        return (is_success, fetch_rows, self.target_point)


# --- 関数 ---
def setup_logger(path, level=logging.DEBUG):
    """
    ロガーの設定を行う

    Args:
        path (str | Path): ログファイルを格納するディレクトリパス
        level (str): ログレベル
    """
    # ログファイルのパスを整形
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    file_path = path / f"debug_{now_str}.log"
    # logsディレクトリがない場合は生成
    file_path.parent.mkdir(parents=True, exist_ok=True)

    # ルートロガーを取得し、ログレベルを設定
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # コンソールハンドラーを作成: ログレベルINFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # ファイルハンドラーを作成: ログレベルDEBUG
    file_handler = logging.FileHandler(file_path)
    file_handler.setLevel(logging.DEBUG)

    # フォーマッタを作成しハンドラーに追加
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(threadName)s - %(lineno)d - %(message)s"
    )

    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # ルートロガーにハンドラーを追加
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)


def validate_params():
    """
    データ抽出に使用する定数及び変数がツールが許容する値であることを確認する

    Args:
        なし
    return:
        なし
    """

    # 検索対象の地点の確認
    for target_date in TARGET_POINTS:
        lat, lng, target_point = target_date
        if not isinstance(lat, float):
            raise ValueError("緯度は小数で設定してください。")
        if not isinstance(lng, float):
            raise ValueError("経度は小数で設定してください。")
        if not MIN_LAT <= lat <= MAX_LAT:
            raise ValueError(
                f"緯度は{MIN_LAT}度〜{MAX_LAT}度の小数で設定してください。"
            )
        if not MIN_LNG <= lng <= MAX_LNG:
            raise ValueError(
                f"経度は{MIN_LNG}度〜{MAX_LNG}度の小数で設定してください。"
            )
        if not isinstance(target_point, str):
            raise ValueError("地点は文字列で設定してください。")

    # 検索範囲の確認
    if not isinstance(SEARCH_RADIUS_M, int):
        raise ValueError("検索範囲は整数で設定してください。")
    if not 0 < SEARCH_RADIUS_M < MAX_SEARCH_RADIUS_M:
        raise ValueError(
            f"検索範囲は{MAX_SEARCH_RADIUS_M}m未満の自然数で設定してください。"
        )

    # BBOXを使った絞り込みの範囲の確認
    if not isinstance(search_radius_padding_factor, float):
        raise ValueError("BBOXを使った絞り込みの範囲は小数で設定してください。")
    # スレッド数の確認
    if not isinstance(MAX_WORKERS, int) or MAX_WORKERS <= 0:
        raise ValueError("スレッド数は自然数で設定してください。")


def get_db_config(env_path):
    """
    .envファイルからDB接続情報を読み込み、辞書型に整形して返却する

    Args:
        env_path (Path | str): .envファイルのパス
    Return:
        config (dict): 辞書型に整形されたDB接続情報
    """

    # .envの環境変数を読み込み
    load_dotenv(env_path)

    # 読み込んだ環境変数を辞書型に整形
    config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }

    # 読み込みに失敗した値がないか確認
    missing_keys = []
    for key, value in config.items():
        if not value:
            missing_keys.append(key)

    if missing_keys:
        logger.error(
            f"【接続エラー】以下の環境変数が未設定です。{', '.join(missing_keys)}"
        )
        sys.exit(1)

    return config


setup_logger(log_dir)
logger = logging.getLogger()

app = FastAPI()


@app.get("/")
async def index():

    return {"message": "Hello Deta!"}


@app.get("/result")
async def get_search_info():
    setup_logger(log_dir)
    logger = logging.getLogger()

    start_time = time.perf_counter()
    logger.info("---- 処理開始 ----")
    # 変数の確認
    try:
        validate_params()
    except ValueError as e:
        logger.error(f"【パラメータエラー】: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    # DB接続情報取得
    db_config = get_db_config(env_dir)

    # マルチスレッドで取得したリストの格納先
    all_combined_rows = []
    # マルチスレッドの成功回数
    success_count = 0

    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS, thread_name_prefix="Thread"
    ) as executor:
        logger.info(f"スレッド処理開始: スレッド数: {MAX_WORKERS}")

        future_to_point = {
            executor.submit(
                ParallelDataFetcher(
                    db_config,
                    (lat, lng),
                    SEARCH_RADIUS_M,
                    search_radius_padding_factor,
                ).run
            ): label
            for lat, lng, label in TARGET_POINTS
        }

        for future in as_completed(future_to_point):
            label = future_to_point[future]

            try:
                is_success, rows, point = future.result()

                if len(rows) > 0:
                    all_combined_rows.extend(rows)
                    logger.info(f"{label}{point}: {len(rows)}件取得 ")
                    success_count += 1
                elif is_success and len(rows) == 0:
                    logger.info(f"{label}{point}: 該当データなし")
                    success_count += 1
                else:
                    logger.error(f"{label}{point}: 実行スレッドでエラー発生")
            except Exception as e:
                logger.error(f"【予期せぬ例外】{label}: {e}")
    logger.info(f"スレッド処理終了: 成功地点 {success_count}/{len(TARGET_POINTS)}")

    end_time = time.perf_counter()
    actual_time = end_time - start_time
    if success_count == len(TARGET_POINTS):
        logger.info(f"---- 正常終了 ---- 実行時間: {actual_time:.3f} 秒 ")
    else:
        logger.info(f"---- 異常終了 ---- 実行時間: {actual_time:.3f} 秒")
    return {"result": all_combined_rows}


@app.post("/")
async def calc(
    data: Data,
):
    result = data.x * data.y
    return {"result": result}
