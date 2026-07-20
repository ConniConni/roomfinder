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

    folium.LayerControl().add_to(m)

    # HTMLファイルを出力
    m.save(file_name)


visualize_on_map_match_properties(target_point)
