import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# このファイルの場所を取得
current_dir = Path(__file__)

# .env(２階層上)を読み込むために該当のディレクトリを取得
project_root = current_dir.parent.parent
print(f"project_root: {project_root}")

# .envの絶対パスを作成
env_path = project_root / ".env"
print(f"env_path: {env_path}")


def get_db_config():
    logger = logging.getLogger(__name__)

    # .envファイル読み込み接続情報を取得
    load_dotenv(env_path)

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


def setup_logging(log_file="debug.log", level=logging.DEBUG):
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
        "%(asctime)s - %(levelname)s - %(lineno)s - %(message)s"
    )
    console_handler.setFormatter(formatter)
    file_handler.setFormatter(formatter)

    # ハンドラにフォーマッタを追加
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
