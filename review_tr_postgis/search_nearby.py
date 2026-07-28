import logging
import os
import sys
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

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
# 取得結果出力先パス
output_dir = Path(__file__).parent / "result" / "search_results.csv"
# .envファイルのパス
env_dir = Path(__file__).parent.parent / ".env"


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
        "%(asctime)s - %(levelname)s - %(threadName)s - %(threadName)s - %(lineno)d - %(message)s"
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
            logger.error("緯度は小数で設定してください。")
            sys.exit(1)
        if not isinstance(lng, float):
            logger.error("経度は小数で設定してください。")
        if not MIN_LAT <= lat <= MAX_LAT:
            logger.error(f"緯度は{MIN_LAT}度〜{MAX_LAT}度の小数で設定してください。")
            sys.exit(1)
        if not MIN_LNG <= lng <= MAX_LNG:
            logger.error(f"経度は{MIN_LNG}度〜{MAX_LNG}度の小数で設定してください。")
            sys.exit(1)
        if not isinstance(target_point, str):
            logger.error("地点は文字列で設定してください。")
            sys.exit(1)

    # 検索範囲の確認
    if not isinstance(SEARCH_RADIUS_M, int):
        logger.error("検索範囲は整数で設定してください。")
        sys.exit(1)
    if not 0 < SEARCH_RADIUS_M < MAX_SEARCH_RADIUS_M:
        logger.error(
            f"検索範囲は{MAX_SEARCH_RADIUS_M}m未満の自然数で設定してください。"
        )
        sys.exit(1)

    # BBOXを使った絞り込みの範囲の確認
    if not isinstance(search_radius_padding_factor, float):
        logger.error("BBOXを使った絞り込みの範囲は小数で設定してください。")
        sys.exit(1)
    # スレッド数の確認
    if not isinstance(MAX_WORKERS, int) or MAX_WORKERS <= 0:
        logger.error("スレッド数は自然数で設定してください。")
        sys.exit(1)
    # データ出力先のパスの確認
    if not output_dir.parent.exists():
        logger.error("ツールと同じ階層にresultディレクトリを作成してください。")
        sys.exit(1)


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


def save_to_csv(file_path, fetch_list):
    """
    データの取得結果をCSVで保存する
    Args:
        file_path (Path | str): CSVファイルのパス
        fetch_list (list): 取得したデータのリスト
    Return:
        なし
    """


if __name__ == "__main__":
    # ロガー取得
    setup_logger(log_dir)
    logger = logging.getLogger()
    # 変数の確認
    validate_params()
    # DB接続情報取得
    db_config = get_db_config(env_dir)
