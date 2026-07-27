import logging
import os
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# --- 変数 ---
# ログファイル格納先
log_dir = Path(__file__).parent / "logs"


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


def get_db_config():
    """
    .envファイルからDB接続情報を読み込み、辞書型に整形して返却する

    Args:
        なし
    Return:
        db_config (dict): 辞書型に整形されたDB接続情報
    """

    # .envの環境変数を読み込み
    load_dotenv()

    # 読み込んだ環境変数を辞書型に整形
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }


if __name__ == "__main__":
    # ロガー取得
    setup_logger(log_dir)
    logger = logging.getLogger()
