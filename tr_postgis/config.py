import logging
import os
import sys
from pathlib import Path
from tkinter import CURRENT
from dotenv import load_dotenv

# .env(２階層上)を読み込むために該当のディレクトリを取得
CURRENT_DIR = Path(__file__)
PROJECT_ROOT_DIR = CURRENT_DIR.parent.parent
# .envの絶対パスを作成
ENV_PATH = PROJECT_ROOT_DIR / ".env"
# ログフォルダの絶対パスを作成
LOG_DIR = CURRENT_DIR.parent / "log"

# ログレベルを設定
LOG_LEVEL = logging.DEBUG


def get_db_config():
    logger = logging.getLogger(__name__)

    # .envファイル読み込み接続情報を取得
    load_dotenv(ENV_PATH)

    # .envから値を取得し、psycopg2の接続処理に使用する引数の形にまとめる
    db_config = {
        "host": os.getenv("POSTGRES_HOST", "localhost"),
        "port": os.getenv("POSTGRES_PORT"),
        "database": os.getenv("POSTGRES_DB"),
        "user": os.getenv("POSTGRES_USER"),
        "password": os.getenv("POSTGRES_PASSWORD"),
    }
    missing_keys = []
    for key, value in db_config.items():
        if not value:
            missing_keys.append(key)

    if missing_keys:
        logger.error(f"設定エラー: 以下の環境変数が空です: {', '.join(missing_keys)}")
        logger.error(".envファイルの設定を確認してください。")
        sys.exit(1)

    return db_config


def setup_logging(log_file=LOG_DIR / "debug.log", level=LOG_LEVEL):
    # ルートロガーを取得
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # コンソールハンドラを作成: ログレベルはINFO
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # ファイルハンドラを作成: ログレベルはDEBUG
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    # フォーマッタを作成
    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(name)s - %(lineno)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # ハンドラにフォーマッタを追加
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
