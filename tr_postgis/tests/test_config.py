import pytest

import config


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
        "設定エラー: 以下の環境変数が空です: port",
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
        "設定エラー: 以下の環境変数が空です: database",
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
        "設定エラー: 以下の環境変数が空です: user",
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
        "設定エラー: 以下の環境変数が空です: password",
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
        "設定エラー: 以下の環境変数が空です: port, user",
        ".envファイルの設定を確認してください。",
    ]
    # 検証
    with pytest.raises(SystemExit) as e:
        config.get_db_config()

    # 終了ステータスが 1 であること
    assert e.value.code == 1
    # ログメッセージが期待結果と一致すること
    assert caplog.messages == expected_logs
