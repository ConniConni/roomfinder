import logging

# 子ロガーを作成
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# コンソールハンドラを作成: ログレベルはINFO
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# ファイルハンドラを作成: ログレベルはDEBUG
file_handler = logging.FileHandler("debug.log")
file_handler.setLevel(logging.DEBUG)

# フォーマッタを作成
formatter = logging.Formatter("%(asctime)s : %(levelname)s : %(message)s")
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)

# ハンドラにフォーマッタを追加
logger.addHandler(console_handler)
logger.addHandler(file_handler)
