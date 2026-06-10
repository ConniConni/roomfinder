import pandas as pd
import random

# 設定：生成するサンプル数
NUM_SAMPLES = 100


def generate_fukuoka_spatial_data(num_samples=100):
    # 福岡市のおおよその中心座標（天神付近）
    # 緯度: 33.5902, 経度: 130.4017
    # この周辺にランダムにプロットするための範囲設定
    lat_min, lat_max = 33.5500, 33.6200
    lon_min, lon_max = 130.3300, 130.4500

    prefixes = [
        "レジデンス",
        "パークサイド",
        "メゾン",
        "コンフォート",
        "アーバン",
        "グランド",
    ]
    suffixes = ["天神", "博多", "大濠", "西新", "赤坂", "薬院", "千早"]

    data = []

    for i in range(1, num_samples + 1):
        # 物件名
        name = f"{random.choice(prefixes)}{random.choice(suffixes)}{random.randint(1, 100)}"

        # 家賃 (4万〜20万円)
        rent = random.randint(40, 200) * 1000

        # 緯度経度をランダムに生成
        lat = random.uniform(lat_min, lat_max)
        lon = random.uniform(lon_min, lon_max)

        # geomカラム用 (WKT形式: POINT(経度 緯度))
        # SQLのGEOMETRY(Point, 4326)にそのまま入れやすい形式
        geom = f"POINT({lon:.6f} {lat:.6f})"

        data.append({"id": i, "name": name, "rent": rent, "geom": geom})

    return pd.DataFrame(data)


# データ生成
df = generate_fukuoka_spatial_data(NUM_SAMPLES)

# CSVとして保存
file_name = "properties_sample.csv"
df.to_csv(file_name, index=False, encoding="utf-8")

print(f"'{file_name}' を生成しました。")
print(df.head())
