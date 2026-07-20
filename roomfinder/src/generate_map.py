import folium

target_point = (130.402333, 33.591472)  # アクロス
file_name = "map_output.html"


def visualize_on_map_match_properties(point):
    target_lng = point[0]
    target_lat = point[1]
    m = folium.Map(location=[target_lat, target_lng], zoom_start=15)

    # 中心点にマーカーを追加
    folium.Marker(
        location=[target_lat, target_lng],
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

    # 駅グループに駅を追加
    folium.Marker(
        location=[33.589955, 130.379615],
        popup=folium.Popup("大濠公園(1号線(空港線))", max_width=300),
        tooltip="クリックで詳細表示",
        icon=folium.Icon(color="red", icon="train", prefix="fa"),
    ).add_to(group_station)

    # スーパーマーケットグループにスーパーを追加
    folium.Marker(
        location=[33.5912791, 130.3817206],
        popup=folium.Popup("Hazama", max_width=300),
        tooltip="クリックで詳細表示",
        icon=folium.Icon(color="orange", icon="shopping-basket", prefix="fa"),
    ).add_to(group_super_market)

    # 物件グループに物件を追加
    popup_text = f"ラフィーナ大濠<br>近隣情報: 大濠公園 xx m, Hazama xx m"
    folium.Marker(
        location=[33.591033, 130.379752],
        popup=folium.Popup(popup_text, max_width=300),
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


visualize_on_map_match_properties(target_point)
