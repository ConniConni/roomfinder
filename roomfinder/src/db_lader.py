import json
import os
import sys
from pathlib import Path
from pyogrio.errors import DataSourceError

import geopandas as gpd
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from shapely import box

# 読み込み対象のファイルパスを取得
current_dir = Path(__file__).parent
two_levels_up = current_dir.parent.parent
shapefile_path = two_levels_up / "roomfinder/input_data/UTF-8/N02-22_Station.shp"
geojson_path = two_levels_up / "roomfinder/input_data/export.geojson"

FUKUOKA_BBOX = box(130.198072, 33.425124, 130.494834, 33.712839)


def get_db_config_property():
    """envファイルを読み込み、DB接続情報を辞書型で返す"""
    load_dotenv()

    port = os.getenv("POSTGRES_PORT")
    database = os.getenv("POSTGRES_DB")
    user = os.getenv("POSTGRES_USER")
    password = os.getenv("POSTGRES_PASSWORD")

    config = {
        "host": "localhost",
        "port": port,
        "database": database,
        "user": user,
        "password": password,
    }

    return config


def db_connect(**config):
    return psycopg2.connect(**config)


def execute_truncate_query(cur, table):
    query = sql.SQL("TRUNCATE TABLE {} CASCADE;").format(sql.Identifier(table))
    cur.execute(query)
    print(f"EXECUTE SQL: {cur.mogrify(query).decode('utf-8')}")


def execute_insert_query(cur, params, count):
    """
    引数で受け取ったsqlを実行する
    Args:
        cur: カーソル
        params: sqlに埋め込むパラメータ
        count: パラメータの要素数
    """
    query = """
        INSERT INTO railway_stations (name, line_name, geom) VALUES %s;
    """
    execute_values(
        cur,
        query,
        params,
        template="(%s, %s, ST_GeomFromText(%s, 4326))",
    )
    print(f"{count}件のデータを登録しました。")


def execute_insert_query_supermarket(cur, params, count):
    """
    引数で受け取ったsqlを実行する
    Args:
        cur: カーソル
        params: sqlに埋め込むパラメータ
        count: パラメータの要素数
    """
    query = """
        INSERT INTO supermarkets (name, geom) VALUES %s;
    """
    execute_values(
        cur,
        query,
        params,
        template="(%s, ST_GeomFromText(%s, 4326))",
    )
    print(f"{count}件のデータを登録しました。")


def export_shape_file(path):
    """
    引数で受け取ったshapeファイルを読み込む
    Args:
        path: ファイルパス
    return: データ挿入に使用するリスト GeoDataFrame
    """
    gdf = None
    shapefile_path = Path(path)
    try:
        gdf = gpd.read_file(shapefile_path, bbox=FUKUOKA_BBOX, encoding="utf-8")
        print("Shapeファイルの読み込みに成功しました。")

    except DataSourceError as e:
        print(f"ファイルの指定が正しいか確認してください。: \n{e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")

    return gdf


def export_geojson_file(path):
    """
    引数で受け取ったshapeファイルを読み込む
    Args:
        path: ファイルパス
    return: データ挿入に使用するリスト geojson_supermarket
    """
    geojson_path = Path(path)

    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)
        features = geojson["features"]
        gen = (
            (
                features[i]["properties"].setdefault("name", "店名不明"),
                f"POINT({features[i]['geometry']['coordinates'][0]} {features[i]['geometry']['coordinates'][1]})",
            )
            for i in range(len(features))
        )
        # print(features[i]["properties"].setdefault("name", "店名不明"))
        # print(features[i]["geometry"]["coordinates"])
        return gen


def format_data_for_params(gdf):
    """
    受け取ったgdfのデータをクエリのパラメータに使える形に変換する
    Args:
        gdf: shapeファイルを読み取り生成したGeoDataFrame
    return:
        params_list: 変換後のデータのリスト 要素は(name, railway_name, 'POINT(lng lat)')
    """

    # 国土数値情報の鉄道のgeometryはLINESTRINGなのでPOINTに変換するために中心点を取得する
    # 変換前に一度メートル単位の座標系 (EPSG:6670) に変換し、重心を計算後、緯度経度 (EPSG:4326) に戻す
    centroids = gdf.to_crs(epsg=6670).geometry.centroid.to_crs(epsg=4326)
    geometry_wkt = (f"POINT({point.y} {point.x})" for point in centroids)

    params_list = zip(gdf["N02_005"], gdf["N02_003"], geometry_wkt)
    record_count = len(gdf["N02_005"])
    return params_list, record_count


if __name__ == "__main__":
    # ファイルの読み込みに失敗した場合はDB接続せずに異常終了する。
    gdf_shp = export_shape_file(shapefile_path)
    if gdf_shp is None:
        print("[ERROR] 異常終了。")
        sys.exit(1)
    params, record_count = format_data_for_params(gdf_shp)

    supermarket_list = export_geojson_file(geojson_path)

    conn = None
    db_config = get_db_config_property()
    try:
        with db_connect(**db_config) as conn:
            print(f"DB: {db_config['database']} に接続しました。")
            with conn.cursor() as cur:
                execute_truncate_query(cur, "supermarkets")
                execute_insert_query_supermarket(cur, supermarket_list, 220)
                execute_truncate_query(cur, "railway_stations")
                execute_insert_query(cur, params, record_count)

    except psycopg2.OperationalError as e:
        print(f"データベース接続エラー: {e}")
    except psycopg2.IntegrityError as e:
        print(f"データ整合性エラー（重複など）: {e}")
    except psycopg2.Error as e:
        print(f"psycopg2の一般的なエラー: {e}")
    except Exception as e:
        print(f"予期せぬエラー: {e}")
    finally:
        if conn:
            conn.close()
            print(f"DB: {db_config['database']} を接断しました。")
        else:
            print(f"DB接続に失敗しました。")
