import logging
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

# --- 変数 ---
# ログファイル格納先
log_dir = Path(__file__).parent / "logs"
# 単位:度でのざっくりとした絞り込み用の係数
search_radius_padding_factor = SEARCH_RADIUS_M / 111000 * 1.5
# 取得結果出力先パス
output_dir = Path(__file__).parent / "result" / "search_results.csv"


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


if __name__ == "__main__":
    # ロガー取得
    setup_logger(log_dir)
    logger = logging.getLogger()
