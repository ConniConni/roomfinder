import folium
import logging
import psycopg2
from pathlib import Path
from shapely import wkt, get_coordinates


import config

# --- 定数 ---
target_point = (33.591472, 130.402333)  # アクロス
file_name = Path(__file__).parent.parent / "output" / "map_output.html"


# --- ロギング設定 ---
config.setup_logging()
logger = logging.getLogger(__name__)


# --- 関数定義 ---
def connect_db(db_config):
    """
    DBへの接続を確立する

    args:
        db_config (dict): DB接続情報

    return:
        conn (object): 接続オブジェクト
    """

    conn = psycopg2.connect(**db_config)

    if conn:
        logger.info("DB接続")
    return conn


def fetch_data_from_db(conn):
    """
    クエリを実行してデータを取得する

    args:
        conn (object): 接続オブジェクト

    return:
        rows (list): クエリの実行結果
    """
    # 取得したデータの保存先を定義
    rows = []

    # 実行するSQL
    sql = """
        SELECT
            prop.id, prop.name, prop.rent, ST_AsText(prop.geom),
            sta.id, sta.name, sta.line_name, ST_AsText(sta.geom),
            mkt.id, mkt.name, ST_AsText(mkt.geom)
        FROM properties As prop
        INNER JOIN railway_stations As sta
            ON ST_Dwithin(prop.geom, sta.geom, 0.014)
            AND ST_Dwithin(ST_Transform(prop.geom, 6670), ST_Transform(sta.geom, 6670), 1000)
        INNER JOIN supermarkets As mkt
            ON ST_Dwithin(prop.geom, mkt.geom, 0.014)
            AND ST_Dwithin(ST_Transform(prop.geom, 6670), ST_Transform(mkt.geom, 6670),1000);
    """

    with conn.cursor() as cur:
        cur.execute(sql)
        logger.debug(sql)
        rows = cur.fetchall()

    return rows


def wkt_to_lat_lng_list(point_wkt):
    geom = wkt.loads(point_wkt)
    coords = get_coordinates(geom)
    lng = coords[0][0]
    lat = coords[0][1]
    return [lat, lng]


def visualize_on_map_match_properties(point, rows):
    lat, lng = point
    m = folium.Map(location=[lat, lng], zoom_start=15)

    # 中心点にマーカーを追加
    folium.Marker(
        location=[lat, lng],
        popup=folium.Popup("アクロス福岡", max_width=300),
        tooltip="クリックで詳細表示",
    ).add_to(m)

    # 複数のレイヤーを変更可能にする
    folium.TileLayer("CartoDB positron", name="CartoDB positron", show=False).add_to(m)
    folium.TileLayer(
        tiles="https://cyberjapandata.gsi.go.jp/xyz/seamlessphoto/{z}/{x}/{y}.jpg",
        attr="国土地理院",
        name="国土地理院 航空写真",
        show=False,
    ).add_to(m)

    folium.TileLayer(
        tiles="https://cyberjapandata.gsi.go.jp/xyz/pale/{z}/{x}/{y}.png",
        attr="国土地理院",
        name="国土地理院 淡色地図",
        show=False,
    ).add_to(m)

    # 駅グループを作成
    group_station = folium.FeatureGroup(name="駅")
    # スーパーマーケットグループを作成
    group_super_market = folium.FeatureGroup(name="スーパー")
    # 物件グループを作成
    group_properties = folium.FeatureGroup(name="物件")

    properties_summary = {}  # 物件IDをキーにして情報をまとめる辞書
    unique_stations = {}  # 駅IDをキーにして情報をまとめる辞書
    unique_markets = {}  # スーパーIDをキーにして情報をまとめる辞書

    for row in rows:
        (
            properties_name_id,
            properties_name,
            properties_rent,
            properties_point_wkt,
            stations_id,
            stations_name,
            stations_route_name,
            stations_point_wkt,
            super_market_id,
            super_market_name,
            super_market_point_wkt,
        ) = row

        if not properties_name_id in properties_summary:
            properties_summary[properties_name_id] = {
                "name": properties_name,
                "rent": properties_rent,
                "latlng": wkt_to_lat_lng_list(properties_point_wkt),
                "stations": set(),
                "markets": set(),
            }
        properties_summary[properties_name_id]["stations"].add(
            f"{stations_name}({stations_route_name})"
        )
        properties_summary[properties_name_id]["markets"].add(super_market_name)

        if not stations_id in unique_stations:
            unique_stations[stations_id] = {
                "name": f"{stations_name}({stations_route_name})",
                "latlng": wkt_to_lat_lng_list(stations_point_wkt),
            }

        if not super_market_id in unique_markets:
            unique_markets[super_market_id] = {
                "name": super_market_name,
                "latlng": wkt_to_lat_lng_list(super_market_point_wkt),
            }

    for _, info in unique_stations.items():

        # 駅グループに駅を追加
        folium.Marker(
            location=info["latlng"],
            popup=folium.Popup(info["name"], max_width=300),
            tooltip="クリックで詳細表示",
            icon=folium.Icon(color="red", icon="train", prefix="fa"),
        ).add_to(group_station)

    for _, info in unique_markets.items():
        # スーパーマーケットグループにスーパーを追加
        folium.Marker(
            location=info["latlng"],
            popup=folium.Popup(info["name"], max_width=300),
            tooltip="クリックで詳細表示",
            icon=folium.Icon(color="orange", icon="shopping-basket", prefix="fa"),
        ).add_to(group_super_market)

    for _, info in properties_summary.items():
        # 物件グループに物件を追加
        stations_text = ", ".join(info["stations"])
        markets_text = ", ".join(info["markets"])
        popup_html = (
            f"{info['name']}<br>周辺の駅: {stations_text}<br>周辺の店: {markets_text}"
        )
        folium.Marker(
            location=info["latlng"],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip="クリックで詳細表示",
            icon=folium.Icon(color="green", icon="building", prefix="fa"),
        ).add_to(group_properties)

    # Mapインスタンスに駅・スーパーマーケット・物件グループを追加
    group_station.add_to(m)
    group_super_market.add_to(m)
    group_properties.add_to(m)

    folium.LayerControl().add_to(m)
    # HTMLファイルを出力
    m.save(file_name)


# --- メイン処理 ---
def main():
    # DB接続情報を取得
    db_config = config.get_db_config()

    # 正常終了時は自動でcommit
    # エラー発生時は自動でrollback（その後except句の処理）
    # with句を抜けたら自動でカーソルを閉じる
    try:
        conn = None  # 初期化
        # DB接続
        with connect_db(db_config) as conn:
            # データ取得
            fetch_rows = fetch_data_from_db(conn)
            logger.info(f"取得結果: {len(fetch_rows)}件")

        # 1件以上のデータが取れているか確認
        if not fetch_rows:
            logger.info("取得結果が0件のためHTMLの出力をスキップ")
            return
        # 取得したデータが1件以上の場合、CSVに出力
        visualize_on_map_match_properties(target_point, fetch_rows)

    except psycopg2.OperationalError as e:
        logger.error(f"【DB接続エラー】設定を見直してください。:{e}")

    except psycopg2.ProgrammingError as e:
        logger.error(f"【SQL実行エラー】クエリの内容を確認してください。:{e}")

    except psycopg2.Error as e:
        logger.error(f"【その他DBエラー】:{e}")

    finally:
        if conn:
            conn.close()
            logger.info("DB切断")


if __name__ == "__main__":
    main()
