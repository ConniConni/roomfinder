import pytest
from unittest.mock import MagicMock, patch, mock_open
import psycopg2
import sample_postgis_1, config  # テスト対象ファイル


class TestPostGISApp:

    # --- connect_db ---
    @patch("psycopg2.connect")
    def test_01_connect_db_success(self, mock_connect, caplog):
        mock_connect.return_value = MagicMock()
        sample_postgis_1.connect_db({"db": "test"})
        assert "DB接続" in caplog.text

    @patch("psycopg2.connect")
    def test_02_connect_db_fail(self, mock_connect):
        mock_connect.side_effect = psycopg2.OperationalError("Error")
        with pytest.raises(psycopg2.OperationalError):
            sample_postgis_1.connect_db({"db": "test"})

    # --- fetch_data_from_db ---
    def test_03_fetch_success(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [(1, "POINT(0 0)")]
        rows = sample_postgis_1.fetch_data_from_db(mock_conn, "WKT")
        assert len(rows) == 1

    def test_04_fetch_empty(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = []
        rows = sample_postgis_1.fetch_data_from_db(mock_conn, "WKT")
        assert rows == []

    def test_05_fetch_sql_error(self):
        mock_conn = MagicMock()
        mock_cur = mock_conn.cursor.return_value.__enter__.return_value
        mock_cur.execute.side_effect = psycopg2.ProgrammingError("SQL Error")
        with pytest.raises(psycopg2.ProgrammingError):
            sample_postgis_1.fetch_data_from_db(mock_conn, "WKT")

    # --- save_to_csv ---
    @patch("builtins.open", new_callable=mock_open)
    def test_06_save_csv_success(self, mock_file, caplog):
        sample_postgis_1.save_to_csv("path.csv", [[1, "geom"]])
        mock_file.assert_called_once()
        assert "1件 のデータをファイルに書き込みました。" in caplog.text

    # --- validate_target_point ---
    def test_14_get_point_success(self):
        target_point = sample_postgis_1.validate_target_point((35.555, 139.555))
        assert target_point == f"POINT(139.555 35.555)"

    def test_15_get_point_success(self):
        target_point = sample_postgis_1.validate_target_point((20.0, 154.0))
        assert target_point == f"POINT(154.0 20.0)"

    def test_16_get_point_lat_missing(self, caplog):
        with pytest.raises(SystemExit) as e:
            sample_postgis_1.validate_target_point((19.999999, 139.555))
        assert "【設定値エラー】" in caplog.text
        assert e.value.code == 1

    def test_17_get_point_lon_missing(self, caplog):
        with pytest.raises(SystemExit) as e:
            sample_postgis_1.validate_target_point((35.555, 154.000001))
        assert "【設定値エラー】" in caplog.text
        assert e.value.code == 1

    # --- main (フロー制御) ---
    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    @patch("sample_postgis_1.fetch_data_from_db")
    @patch("sample_postgis_1.save_to_csv")
    def test_08_main_success_flow(self, mock_save, mock_fetch, mock_conn_func, _):
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_fetch.return_value = [(1, "geom")]
        sample_postgis_1.main()
        mock_save.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    @patch("sample_postgis_1.fetch_data_from_db")
    @patch("sample_postgis_1.save_to_csv")
    def test_09_main_skip_flow(self, mock_save, mock_fetch, mock_conn_func, _, caplog):
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_fetch.return_value = []  # 0件
        sample_postgis_1.main()
        mock_save.assert_not_called()
        assert "取得結果が0件のためCSVファイルの出力をスキップ" in caplog.text

    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    def test_10_main_op_error(self, mock_conn_func, _, caplog):
        mock_conn_func.side_effect = psycopg2.OperationalError("Conn Fail")
        sample_postgis_1.main()
        assert "【DB接続エラー】" in caplog.text

    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    @patch("sample_postgis_1.fetch_data_from_db")
    def test_11_main_prog_error(self, mock_fetch, mock_conn_func, _, caplog):
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_fetch.side_effect = psycopg2.ProgrammingError("SQL Fail")
        sample_postgis_1.main()
        assert "【SQL実行エラー】" in caplog.text

    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    @patch("sample_postgis_1.fetch_data_from_db")
    def test_12_main_generic_db_error(self, mock_fetch, mock_conn_func, _, caplog):
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        mock_fetch.side_effect = psycopg2.Error("Generic Fail")
        sample_postgis_1.main()
        assert "【その他DBエラー】" in caplog.text

    @patch("sample_postgis_1.config.get_db_config", return_value={})
    @patch("sample_postgis_1.connect_db")
    def test_13_main_finally_close(self, mock_conn_func, _):
        mock_conn = MagicMock()
        mock_conn_func.return_value.__enter__.return_value = mock_conn
        sample_postgis_1.main()
        mock_conn.close.assert_called()

    # --- fetch_data_from_db（境界値テスト） ---
    def test_18_fetch_data_from_db_boundary_value(self):
        """
        クエリの境界値をテスト
        テスト用のDBでクエリを実行すると3件、id=1,2,3のものが取得できることを確認
        """
        db_config = config.get_db_config()
        db_config["database"] = "gis_tr_db_test"
        conn = sample_postgis_1.connect_db(db_config)
        point_wkt = sample_postgis_1.validate_target_point((35.658, 139.745))
        rows = sample_postgis_1.fetch_data_from_db(conn, point_wkt)
        assert len(rows) == 3
        actual_ids = [row[0] for row in rows]
        assert set(actual_ids) == {1, 2, 3}
