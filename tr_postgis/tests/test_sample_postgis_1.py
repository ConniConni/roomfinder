from multiprocessing import process

import pytest
from unittest.mock import MagicMock, patch, mock_open
import psycopg2
import sample_postgis_1, config  # テスト対象ファイル
from pathlib import Path
from sample_postgis_1 import PostGISProcessor

# --- テスト用定数 ---
TEST_DB_CONFIG = {
    "host": "localhost",
    "database": "testdb",
    "user": "user",
    "password": "pass",
}
TEST_TARGET_POINT = (35.658, 139.745)
TEST_RADIUS = 1000
TEST_COEFFICIENT = 0.000014
TEST_CSV_PATH = Path("test_result.csv")


@pytest.fixture
def processor():
    """PostGISProcessorの標準的なテスト用インスタンスを生成するフィクスチャ"""
    return PostGISProcessor(
        db_config=TEST_DB_CONFIG,
        target_point=TEST_TARGET_POINT,
        search_radius=TEST_RADIUS,
        coefficient=TEST_COEFFICIENT,
        csv_path=TEST_CSV_PATH,
    )


class TestPostGISApp:

    # --- connect_db ---
    @patch("psycopg2.connect")
    def test_01_connect_db_success(self, mock_connect, processor, caplog):
        mock_connect.return_value = MagicMock()
        conn = processor.connect_db()
        assert conn == processor.conn
        assert "DB接続" in caplog.text

    @patch("psycopg2.connect")
    def test_02_connect_db_fail(self, mock_connect, processor):
        mock_connect.side_effect = psycopg2.OperationalError("Error")
        with pytest.raises(psycopg2.OperationalError):
            processor.connect_db()

    # --- fetch_data_from_db ---
    def test_03_fetch_success(self, processor):
        mock_conn = MagicMock()
        processor.conn = mock_conn
        mock_cur = processor.conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = [(1, "POINT(0 0)")]
        processor.fetch_data_from_db()
        assert len(processor.fetch_rows) == 1

    def test_04_fetch_empty(self, processor):
        mock_conn = MagicMock()
        processor.conn = mock_conn
        mock_cur = processor.conn.cursor.return_value.__enter__.return_value
        mock_cur.fetchall.return_value = []
        processor.fetch_data_from_db()
        assert processor.fetch_rows == []

    def test_05_fetch_sql_error(self, processor):
        mock_conn = MagicMock()
        processor.conn = mock_conn
        mock_cur = processor.conn.cursor.return_value.__enter__.return_value
        mock_cur.execute.side_effect = psycopg2.ProgrammingError("SQL Error")
        with pytest.raises(psycopg2.ProgrammingError):
            processor.fetch_data_from_db()

    def test_26_conn_error(self, processor):
        with pytest.raises(RuntimeError) as e:
            processor.fetch_data_from_db()
        assert "DB接続が確立されていません。" == str(e.value)

    # --- save_to_csv ---
    @patch("builtins.open", new_callable=mock_open)
    def test_06_save_csv_success(self, mock_file, processor, caplog):
        processor.fetch_rows = [(1, "POINT(0 0)")]
        processor.save_to_csv()
        mock_file.assert_called_once()
        assert "1件 のデータをファイルに書き込みました。" in caplog.text

    # --- validate_target_point ---
    def test_14_get_point_success(self, processor):
        processor.validate_target_point()
        assert processor.point_wkt == f"POINT(139.745 35.658)"

    def test_15_get_point_success(self, processor):
        processor.target_point = (20.0, 154.0)
        processor.validate_target_point()
        assert processor.point_wkt == f"POINT(154.0 20.0)"

    def test_16_get_point_lat_missing(self, processor):
        processor.target_point = (19.999999, 139.555)
        with pytest.raises(ValueError) as e:
            processor.validate_target_point()
        assert "基準点は北緯20°〜45°" in str(e.value)

    def test_17_get_point_lon_missing(self, processor):
        processor.target_point = (19.999999, 139.555)
        with pytest.raises(ValueError) as e:
            processor.validate_target_point()
        assert "基準点は北緯20°〜45°" in str(e.value)

    # --- validate_execution_settings ---
    def test_20_isValidate_execution_settings_success(self, processor):
        processor.validate_execution_settings()
        assert processor.search_radius == 1000
        assert processor.coefficient == 0.000014

    def test_21_isValidate_execution_settings_str_success(self, processor):
        processor.search_radius = "100"
        processor.coefficient = "0.1"
        processor.validate_execution_settings()
        assert processor.search_radius == 100
        assert isinstance(processor.search_radius, int)
        assert processor.coefficient == 0.1
        assert isinstance(processor.coefficient, float)

    def test_22_isValidate_execution_settings_negative_missing(self, processor):
        processor.search_radius = -100
        with pytest.raises(ValueError) as e:
            processor.validate_execution_settings()
        assert "SEARCH_RADIUSは正の整数、" in str(e.value)

    def test_23_isValidate_execution_settings_zero_missing(self, processor):
        processor.coefficient = "0"
        with pytest.raises(ValueError) as e:
            processor.validate_execution_settings()
        assert "COEFFICIENTは正の浮動小数で" in str(e.value)

    def test_24_isValidate_execution_settings_str_missing(self, processor):
        processor.search_radius = "str"
        with pytest.raises(ValueError) as e:
            processor.validate_execution_settings()
        assert "SEARCH_RADIUSは正の整数" in str(e.value)

    def test_25_isValidate_execution_settings_list_missing(self, processor):
        processor.coefficient = [0.1]
        with pytest.raises(ValueError) as e:
            processor.validate_execution_settings()
        assert "COEFFICIENTは正の浮動小数で" in str(e.value)

    # --- run ---
    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_08_run_success_flow(
        self, mock_save, mock_fetch, mock_conn_func, processor
    ):
        # 接続オブジェクトの代わりとなるモックを作成
        mock_conn = MagicMock()
        # connect_dbが呼ばれたらモックを返す
        mock_conn_func.return_value = mock_conn
        # with構文でも同じモックを返す
        mock_conn.__enter__.return_value = mock_conn
        processor.conn = mock_conn
        processor.fetch_rows = [(1, "POINT(0 0)")]

        result = processor.run()

        assert result is True
        mock_fetch.assert_called_once()
        mock_save.assert_called_once()
        mock_conn.close.assert_called_once()

    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_09_run_skip_flow(
        self, mock_save, mock_fetch, mock_conn_func, processor, caplog
    ):
        mock_conn = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        processor.conn = mock_conn
        processor.fetch_rows = []  # 0件

        result = processor.run()

        assert result is True
        assert "取得結果が0件のためCSVファイルの出力をスキップ" in caplog.text
        mock_fetch.assert_called_once()
        mock_save.assert_not_called()
        mock_conn.close.assert_called_once()

    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_10_run_op_error(
        self, mock_save, mock_fetch, mock_conn_func, processor, caplog
    ):
        mock_conn_func.side_effect = psycopg2.OperationalError("Conn Fail")

        result = processor.run()
        assert result is False
        assert "【DB接続エラー】" in caplog.text
        mock_fetch.assert_not_called()
        mock_save.assert_not_called()

    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_11_run_prog_error(
        self, mock_save, mock_fetch, mock_conn_func, processor, caplog
    ):
        mock_conn = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        processor.conn = mock_conn
        mock_fetch.side_effect = psycopg2.ProgrammingError("SQL Fail")

        result = processor.run()

        assert result is False
        assert "【SQL実行エラー】" in caplog.text
        mock_save.assert_not_called()
        mock_conn.close.assert_called_once()

    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_12_run_generic_db_error(
        self, mock_save, mock_fetch, mock_conn_func, processor, caplog
    ):
        mock_conn = MagicMock()
        mock_conn_func.return_value = mock_conn
        mock_conn.__enter__.return_value = mock_conn
        processor.conn = mock_conn
        mock_fetch.side_effect = psycopg2.Error("Generic Fail")
        result = processor.run()
        assert result is False
        assert "【その他DBエラー】" in caplog.text
        mock_save.assert_not_called()
        mock_conn.close.assert_called_once()

    @patch.object(PostGISProcessor, "connect_db")
    @patch.object(PostGISProcessor, "fetch_data_from_db")
    @patch.object(PostGISProcessor, "save_to_csv")
    def test_13_run_value_error(
        self, mock_save, mock_fetch, mock_conn_func, processor, caplog
    ):
        processor.target_point = (19.999999, 139.555)
        result = processor.run()
        assert result is False
        assert "【設定値エラー】" in caplog.text
        mock_conn_func.assert_not_called()
        mock_fetch.assert_not_called()
        mock_save.assert_not_called()

    # --- main (フロー制御) ---
    @patch("config.get_db_config", return_value={"db": "test"})
    @patch.object(PostGISProcessor, "run")
    def test_27_main_success(self, mock_run, _, caplog):
        mock_run.return_value = True
        sample_postgis_1.main()
        assert "---- 正常終了 ----" in caplog.text

    @patch("config.get_db_config", return_value={"db": "test"})
    @patch.object(PostGISProcessor, "run")
    def test_28_main_fail(self, mock_run, _, caplog):
        mock_run.return_value = False
        sample_postgis_1.main()
        assert "---- 異常終了 ----" in caplog.text

    # --- fetch_data_from_db（境界値テスト） ---
    def test_18_fetch_data_from_db_boundary_value(self, processor):
        """
        クエリの境界値をテスト
        テスト用のDBでクエリを実行すると3件、id=1,2,3のものが取得できることを確認
        """
        db_config = config.get_db_config()
        db_config["database"] = "gis_tr_db_test"
        processor.db_config = db_config
        processor.point_wkt = "POINT(139.745 35.658)"
        processor.search_radius = 1000
        processor.coefficient = 0.000014
        processor.connect_db()
        processor.fetch_data_from_db()
        assert len(processor.fetch_rows) == 3
        actual_ids = [row[0] for row in processor.fetch_rows]
        assert set(actual_ids) == {1, 2, 3}

    def test_19_fetch_data_from_db_execute_setting_value(self, processor):
        """
        クエリのパラメータとなる設定値を変更した場合、取得結果が変わることを確認
        テスト用のDBでクエリを実行すると1件、id=1のものが取得できることを確認
        """
        db_config = config.get_db_config()
        db_config["database"] = "gis_tr_db_test"
        processor.db_config = db_config
        processor.point_wkt = "POINT(139.745 35.658)"
        processor.search_radius = 500.1
        processor.coefficient = 0.000014
        processor.connect_db()
        processor.fetch_data_from_db()
        assert len(processor.fetch_rows) == 1
        actual_ids = [row[0] for row in processor.fetch_rows]
        assert set(actual_ids) == {1}
