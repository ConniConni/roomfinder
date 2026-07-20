import folium
from shapely import wkt, get_coordinates

target_point = (33.591472, 130.402333)  # アクロス
file_name = "map_output.html"

# visualize_on_map_match_properties()のロジック確認用のリスト
test_properties_data = [
    # (物件ID, 物件名, 家賃, 物件座標, 駅ID, 駅名, 路線名, 駅座標, スーパーID, スーパー名, スーパー座標)
    # 物件1: 赤坂駅・サニー赤坂
    (
        1,
        "レジデンス赤坂タワー",
        85000,
        "POINT(130.391 33.588)",
        101,
        "赤坂駅",
        "空港線",
        "POINT(130.394 33.587)",
        201,
        "サニー 赤坂店",
        "POINT(130.392 33.589)",
    ),
    # 物件2: 大濠公園駅・マックスバリュ
    (
        2,
        "大濠パークサイドマンション",
        120000,
        "POINT(130.378 33.590)",
        102,
        "大濠公園駅",
        "空港線",
        "POINT(130.379 33.589)",
        202,
        "マックスバリュ エクスプレス大濠店",
        "POINT(130.377 33.591)",
    ),
    # 物件3: 【駅が2つある場合】レコードが2行になります（これがJOINの特徴です）
    (
        3,
        "天神ビジネスセンターレジデンス",
        150000,
        "POINT(130.400 33.592)",
        103,
        "天神駅",
        "空港線",
        "POINT(130.401 33.591)",
        203,
        "イオンショッパーズ福岡",
        "POINT(130.399 33.594)",
    ),
    (
        3,
        "天神ビジネスセンターレジデンス",
        150000,
        "POINT(130.400 33.592)",
        101,
        "赤坂駅",
        "空港線",
        "POINT(130.394 33.587)",
        203,
        "イオンショッパーズ福岡",
        "POINT(130.399 33.594)",
    ),
    # 物件4: 薬院駅・ボンラパス
    (
        4,
        "薬院サウスガーデン",
        95000,
        "POINT(130.400 33.582)",
        104,
        "薬院駅",
        "七隈線",
        "POINT(130.402 33.581)",
        204,
        "ボンラパス 薬院店",
        "POINT(130.399 33.583)",
    ),
    # 物件5: 舞鶴（駅もスーパーも重複）
    (
        5,
        "舞鶴アパートメント",
        70000,
        "POINT(130.392 33.592)",
        101,
        "赤坂駅",
        "空港線",
        "POINT(130.394 33.587)",
        201,
        "サニー 赤坂店",
        "POINT(130.392 33.589)",
    ),
]


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
            unique_markets[stations_id] = {
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


visualize_on_map_match_properties(target_point, test_properties_data)
