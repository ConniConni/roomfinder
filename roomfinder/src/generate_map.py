import folium

target_point = (130.402333, 33.591472)  # アクロス
file_name = "map_output.html"


def visualize_on_map_match_properties(point):
    target_lng = point[0]
    target_lat = point[1]
    m = folium.Map(location=[target_lat, target_lng], zoom_start=15)
    m.save(file_name)


visualize_on_map_match_properties(target_point)
