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
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

import config

# --- 定数 ---
# 基準点
TARGET_LOCATIONS = [
    (35.658, 139.745, "東京タワー"),
    (35.710, 139.810, "スカイツリー"),
    (35.681, 139.767, "東京駅"),
    (43.062, 141.353, "札幌市時計台"),
    (40.828, 140.748, "ねぶたの家 ワ・ラッセ"),
    (36.562, 136.662, "兼六園"),
    (34.665, 135.432, "ユニバーサル・スタジオ・ジャパン"),
    (34.185, 133.819, "金刀比羅宮（御本宮）"),
    (34.296, 132.320, "嚴島神社（宮島）"),
    (33.515, 130.534, "太宰府天満宮"),
    (26.217, 127.714, "首里城正殿跡"),
]
# 検索距離
SEARCH_RADIUS = 1000
# 度(°)をメートル(m)に変換する際の係数 北端の北緯45°が0.000013度のためマージンを足した固定値に
COEFFICIENT = 0.000014
# スレッド生成数
MAX_WORKERS = 3
# スレッド名
THREAD_NAME_PREFIX = "Thread"

# 実行結果ファイル名: ./tr_postgis/result/extraction_point.csv
CSV_FILE_NAME = Path(__file__).parent / "result" / "extraction_point.csv"

# --- ロギング設定 ---
config.setup_logging()
logger = logging.getLogger(__name__)


# --- クラス定義 ---
class PostGISProcessor:
    """基準点から指定の距離内にある点をCSVファイルに出力するクラス

    以下の処理をメソッドとして持つ
        設定値が意図した型、範囲であるかを検証
        DB接続処理
        クエリの実行

    Args:
        db_config (dict): DB接続情報
        target_point (tuple): 基準点の座標。形式は (緯度, 経度) の float タプル
        search_radius (int | str): 検索距離
        coefficient (float| int | str): マージンを考慮したメートルを度に変換する係数
    """

    def __init__(
        self,
        db_config,
        target_point,
        search_radius,
        coefficient,
    ):
        """インスタンス変数で初期化するクラス変数"""
        self.db_config = db_config
        self.target_point = target_point
        self.search_radius = search_radius  # クラスメソッドで整数型に変換する
        self.coefficient = coefficient  # クラスメソッドで浮動小数型に変換する

        """クラスメソッドで扱うクラス変数"""
        self.conn = None
        self.point_wkt = None
        self.fetch_rows = []
        self.is_success_flg = False

    def connect_db(self):
        """
        DBへの接続を確立する

        return:
            conn (object): 接続オブジェクト
        """

        self.conn = psycopg2.connect(**self.db_config)

        if self.conn:
            logger.info("DB接続")

        return self.conn

    def fetch_data_from_db(self):
        """
        クエリを実行してデータを取得する
        """

        # 検索半径（m）をマージン付きの経緯度（度）に変換
        expand_deg = self.search_radius * self.coefficient

        # 実行するSQL
        sql = """
            SELECT id, ST_AsText(geom) AS geom
            FROM training_data
            WHERE geom && ST_Expand(ST_GeomFromText(%(point_wkt)s, 4326), %(deg)s)
            AND ST_DWithin(
                geom::geography,
                ST_GeogFromText(%(point_wkt)s),
                %(dist)s
            )
            ORDER BY id;
        """

        if self.conn is None:
            raise RuntimeError("DB接続が確立されていません。")

        with self.conn.cursor() as cur:
            cur.execute(
                sql,
                {
                    "point_wkt": self.point_wkt,
                    "deg": expand_deg,
                    "dist": self.search_radius,
                },
            )
            log_msg_sql = cur.mogrify(
                sql,
                {
                    "point_wkt": self.point_wkt,
                    "deg": expand_deg,
                    "dist": self.search_radius,
                },
            ).decode("utf-8")
            logger.debug(log_msg_sql)
            self.fetch_rows = cur.fetchall()

    def validate_target_point(self):
        """
        基準点が日本国内（北緯20°〜45°、東経122°〜154°の間）かチェックする

        Raises:
            基準点が範囲外の場合、独自エラーを呼び出し元に投げる。
        """
        lat, lon = self.target_point
        if 20 <= lat <= 45 and 122 <= lon <= 154:
            self.point_wkt = f"POINT({lon} {lat})"
        else:
            raise ValueError(
                "基準点は北緯20°〜45°、東経122°〜154°の間の数値で設定してください。"
            )

    def validate_execution_settings(self):
        """
        実行時の設定（距離、係数）が型変換可能か確認することで妥当性をチェックする

        Raises:
            正しく型変換できないもしくは負の数の場合、独自エラーを呼び出し元に投げる
        """
        # 距離のチェック
        try:
            self.search_radius = int(self.search_radius)
            self.coefficient = float(self.coefficient)

            # 設定値が負の数だった場合はValueErrorを投げる
            if self.search_radius <= 0 or self.coefficient <= 0:
                raise ValueError

        except (ValueError, TypeError):
            raise ValueError(
                "SEARCH_RADIUSは正の整数、COEFFICIENTは正の浮動小数で設定してください。\n"
                f"SEARCH_RADIUS: {self.search_radius!r}, COEFFICIENT:{self.coefficient!r}"
            )

    def run(self):
        """
        実行関数

        returns:
            self.is_success_flg (boolean): 処理成功フラグ
            self.fetch_rows (list): 該当地点の取得結果のリスト
        """
        start_time = time.perf_counter()
        try:
            self.validate_target_point()
            self.validate_execution_settings()

            with self.connect_db() as conn:
                # データ取得
                self.fetch_data_from_db()

            self.is_success_flg = True

        except ValueError as e:
            logger.error(f"【設定値エラー】{e}")
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

            end_time = time.perf_counter()
            actual_time = end_time - start_time
            logger.info(f"実行時間: {actual_time:.3f} 秒")

        return self.is_success_flg, self.fetch_rows, self.target_point


# --- CSV書き込み処理 ---
def save_to_csv(csv_path, rows):
    """
    CSVファイルにヘッダー付きでリストのデータを書き込む
    args:
        csv_path (str | Path): 読み込むCSVファイルのパス
        rows (list): 書き込み対象のリスト
    """
    header = ["id", "geom"]
    with open(csv_path, mode="w", encoding="utf-8", newline="") as f:
        write = csv.writer(f)
        # ヘッダー書き込み
        write.writerow(header)
        # 取得したidとgeomを書き込み
        write.writerows(rows)
        logger.info(f"{len(rows)}件 のデータをファイルに書き込みました。")


# --- メイン処理 ---
def main():
    start_time = time.perf_counter()
    logger.info("---- 処理開始 ----")
    # DB接続情報を取得
    db_config = config.get_db_config()

    logger.info("---- マルチスレッド処理開始 ----")
    # マルチスレッドで取得したリストの格納先
    all_combined_rows = []
    # マルチスレッドの成功回数
    success_count = 0
    with ThreadPoolExecutor(
        max_workers=MAX_WORKERS, thread_name_prefix=THREAD_NAME_PREFIX
    ) as executor:
        # スレッドに地点ごとに処理を投入
        future_to_point = {
            executor.submit(
                PostGISProcessor(db_config, (lat, lon), SEARCH_RADIUS, COEFFICIENT).run
            ): label
            for lat, lon, label in TARGET_LOCATIONS
        }

        # スレッドが完了したら結果を取得
        for future in as_completed(future_to_point):
            label = future_to_point[future]
            try:
                success, rows, point = future.result()
                if success and len(rows) > 0:
                    logger.info(f"{label}({point}): {len(rows)} 件取得")
                    all_combined_rows.extend(rows)
                    success_count += 1
                elif success and len(rows) == 0:
                    logger.info(f"{label}({point}): 該当データなし")
                    success_count += 1
                else:
                    logger.error(
                        f"【エラー】{label}({point})の実行スレッドでエラー発生"
                    )
            except Exception as e:
                logger.error(f"【予期せぬ例外】{label}: {e}")

    logger.info(f"全スレッド終了。成功地点: {success_count}/{len(TARGET_LOCATIONS)}")

    # 1件以上のデータが取れている場合はCSV書き込み
    if len(all_combined_rows) > 0:
        # 取得したデータが1件以上の場合、CSVに出力
        save_to_csv(CSV_FILE_NAME, all_combined_rows)
    # SQL実行でエラーが発生していないが、取得データ数が0件の場合は、CSV書き込み処理をスキップ
    if success_count == len(TARGET_LOCATIONS) and len(all_combined_rows) == 0:
        logger.info("取得結果が0件のためCSVファイルの出力をスキップ")

    end_time = time.perf_counter()
    actual_time = end_time - start_time
    if success_count == len(TARGET_LOCATIONS):
        logger.info(f"---- 正常終了 ---- 実行時間: {actual_time:.3f} 秒 ")
    else:
        logger.info(f"---- 異常終了 ---- 実行時間: {actual_time:.3f} 秒")


if __name__ == "__main__":
    main()
