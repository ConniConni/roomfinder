import logging


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
