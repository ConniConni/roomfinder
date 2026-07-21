import pytest
import logging
import config
from datetime import datetime
from pathlib import Path


# ----- get_db_config() のテストコード-----
def test_get_db_config_success(monkeypatch):
    """
    ID: C-N1 (正常系)
    テスト項目：全項目（HOST/PORT/DB/USER/PASS）設定済み
    期待結果：正しく辞書形式で返却されること
    """
    # テスト用の環境変数をセット
    monkeypatch.setenv("POSTGRES_HOST", "test_host")
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    # 実行
    db_config = config.get_db_config()

    # 検証
    assert db_config["host"] == "test_host"
    assert db_config["port"] == "5432"
    assert db_config["database"] == "test_db"
    assert db_config["user"] == "test_user"
    assert db_config["password"] == "test_pass"


def test_get_db_config_success_host_default(monkeypatch):
    """
    ID: C-N2 (正常系)
    テスト項目：POSTGRES_HOST が未設定
    期待結果：デフォルト値 localhost が適用されること
    """

    # テスト用の環境変数をセット
    monkeypatch.setenv("POSTGRES_PORT", "5432")
    monkeypatch.setenv("POSTGRES_DB", "test_db")
    monkeypatch.setenv("POSTGRES_USER", "test_user")
    monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")

    # 実行
    db_config = config.get_db_config()

    # 検証
    assert db_config["host"] == "localhost"


def test_get_db_config_raises_exit_when_port_missing(monkeypatch, caplog):
    """
    ID: E-N1 (異常系)
    テスト項目：POSTGRES_PORT が未設定
    期待結果：エラーログ出力後、ステータス 1 で終了すること
    """

    # テスト用の環境変数をセット
    monkeypatch.delenv("POSTGRES_PORT", raising=False)

    # 期待されるログリストを定義
    expected_logs = [
        "【設定エラー】以下の環境変数が空です: port",
        ".envファイルの設定を確認してください。",
    ]

    # 検証
    # sys.exit(1) が呼ばれることを検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であることを確認
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs


def test_get_db_config_raises_exit_when_database_missing(monkeypatch, caplog):
    """
    ID: E-N2 (異常系)
    テスト項目：POSTGRES_DB が未設定
    期待結果：エラーログ出力後、ステータス 1 で終了すること
    """

    # テスト用の環境変数をセット
    monkeypatch.delenv("POSTGRES_DB", raising=False)

    # 期待されるログリストを定義
    expected_logs = [
        "【設定エラー】以下の環境変数が空です: database",
        ".envファイルの設定を確認してください。",
    ]
    # 検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs


def test_get_db_config_raises_exit_when_user_missing(monkeypatch, caplog):
    """
    ID: E-N3 (異常系)
    テスト項目：POSTGRES_USER が未設定
    期待結果：エラーログ出力後、ステータス 1 で終了すること
    """

    # テスト用の環境変数をセット
    monkeypatch.delenv("POSTGRES_USER", raising=False)

    # 期待されるログリストを定義
    expected_logs = [
        "【設定エラー】以下の環境変数が空です: user",
        ".envファイルの設定を確認してください。",
    ]
    # 検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs


def test_get_db_config_raises_exit_when_password_missing(monkeypatch, caplog):
    """
    ID: E-N4 (異常系)
    テスト項目：POSTGRES_DB が未設定
    期待結果：エラーログ出力後、ステータス 1 で終了すること
    """

    # テスト用の環境変数をセット
    monkeypatch.delenv("POSTGRES_PASSWORD", raising=False)

    # 期待されるログリストを定義
    expected_logs = [
        "【設定エラー】以下の環境変数が空です: password",
        ".envファイルの設定を確認してください。",
    ]
    # 検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs


def test_get_db_config_raises_exit_when_multiple_missing(monkeypatch, caplog):
    """
    ID: E-N5 (異常系)
    テスト項目：複数の必須項目が未設定(host, port, user)
    期待結果：エラーログ出力後、ステータス 1 で終了すること
    """

    # テスト用の環境変数をセット
    monkeypatch.delenv("POSTGRES_HOST", raising=False)
    monkeypatch.delenv("POSTGRES_PORT", raising=False)
    monkeypatch.delenv("POSTGRES_USER", raising=False)

    # 期待されるログリストを定義
    expected_logs = [
        "【設定エラー】以下の環境変数が空です: port, user",
        ".envファイルの設定を確認してください。",
    ]
    # 検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs


@pytest.fixture(autouse=True)
def cleanup_logging():
    """テスト開始前と終了後に、ルートロガーのハンドラを完全に空にする"""
    root_logger = logging.getLogger()

    # テスト開始前にクリア
    root_logger.handlers.clear()

    yield  # テスト実行

    # テスト終了後にも念のためクリア
    root_logger.handlers.clear()


def test_setup_logging_success(monkeypatch):
    """
    ID: CS-N1, CS-N2, CS-N4 (正常系)
    テスト項目：ルートロガーの設定確認/ハンドラの構成確認/ログファイルの作成
    期待結果：ログレベルが DEBUG に設定されること/ハンドラが２つ生成されること/ "tests/log/debug_YYYYMMDD_HHMMSS.log" 形式でファイルが生成される
    """
    # tests/log フォルダを指定
    now_str = datetime.now().strftime("%Y%m%d_%H%M%S")
    TEST_LOG_DIR = Path(__file__).parent / "logs" / now_str

    # config.LOG_DIR を tests/logs に差し替える
    monkeypatch.setattr(config, "LOG_DIR", TEST_LOG_DIR)

    # 実行（config内でmkdirしていない場合は、テスト側で作成が必要）
    TEST_LOG_DIR.mkdir(parents=True, exist_ok=True)
    config.setup_logging()

    # --- 検証 ---
    root_logger = logging.getLogger()

    # CS-N1: レベル確認
    assert root_logger.level == logging.DEBUG

    # CS-N2: ハンドラ数確認
    my_handlers = [
        h
        for h in root_logger.handlers
        if "LogCaptureHandler" not in h.__class__.__name__
    ]
    assert len(my_handlers) == 2

    # CS-N4: 実際にファイルが作られたか確認
    log_files = list(TEST_LOG_DIR.glob("debug_*.log"))
    assert len(log_files) >= 1

    print(f"\nチェック用: ログファイルが作成されました -> {log_files[0]}")


def test_setup_logging_when_log_not_exist(monkeypatch, capsys):
    """
    ID: CS-N5 (異常系)
    テスト項目：logsディレクトリの確認
    期待結果：logs/ が存在しない場合、エラーとなること
    """
    # テスト用の存在しないdummy_logsのパスを生成
    TEST_LOG_DIR = Path(__file__).parent / "dummy_logs"
    # config.LOG_DIR を tests/dummy_logs に差し替える
    monkeypatch.setattr(config, "LOG_DIR", TEST_LOG_DIR)

    expected_message = "【エラー】logsディレクトリを作成して再実行してください。"
    # --- 検証 ---
    with pytest.raises(SystemExit) as e:
        config.setup_logging()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # コンソールのメッセージが期待結果と一致すること
    assert capsys.readouterr().err == expected_message
