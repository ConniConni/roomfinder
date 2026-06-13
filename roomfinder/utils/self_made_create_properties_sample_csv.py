"""
id, name, rent, geomをカラムとするデータフフレームを生成する関数
id: 自動採番
name: ランダムな文字列の結合
rent: 4万〜20万円 1000円刻み
geom: POINT({lng} {lat})

lat_min, lat_max = 33.425124, 33.712839
lon_min, lon_max = 130.198072, 130.494834

prefixes = [
        "レジデンス",
        "パークサイド",
        "メゾン",
        "コンフォート",
        "アーバン",
        "グランド",
    ]
suffixes = ["天神", "博多", "大濠", "西新", "赤坂", "薬院", "千早"]

# CSV出力にはpandasのto_csv()メソッドを利用
"""

import random
import pandas as pd
from pathlib import Path

current_dir = Path(__file__).parent
two_levels_up = current_dir.parent.parent
csv_file_path = two_levels_up / "roomfinder/input_data/properties_sample.csv"
record_num = 100


def generate_fukuoka_spatial_data(num_sample=100):
    """
    指定の数だけレコードを持つデータフレームを返却する
    Args: num_sample
        csvファイルのデータ数を指定する。未指定の場合は100とする
    return df
        id, name, rent, geomをカラムとするデータフレーム
    """

    lat_min, lat_max = 33.425124, 33.712839
    lng_min, lng_max = 130.198072, 130.494834

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

    for i in range(1, num_sample + 1):
        name = f"{random.choice(prefixes)}{random.choice(suffixes)}{random.randint(1, 100)}"
        rent = random.randint(40, 200) * 1000
        lng = random.uniform(lng_min, lng_max)
        lat = random.uniform(lat_min, lat_max)
        geom_wkt = f"POINT({lng:.6f} {lat:.6f})"
        data.append({"id": i, "name": name, "rent": rent, "geom": geom_wkt})

    df = pd.DataFrame(data)

    return df


df = generate_fukuoka_spatial_data(record_num)
print(df.head())
df.to_csv(csv_file_path, index=False, encoding="utf-8")
print(f"{record_num}件のデータをもつcsvを出力しました。")
