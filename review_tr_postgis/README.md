## 課題：高負荷対応「近傍施設検索エンジン」の構築 (Python版)

### 1. システム要件

#### A. データベース設計

以下のカラムを持つ `stores` テーブルを作成してください。

- `id`: シリアル型（主キー）
- `name`: 文字列（店舗名）
- `category`: 文字列（カテゴリ：例 `restaurant`, `cafe`, `shop`）
- `geom`: `GEOMETRY(Point, 4326)` 型
- **必須:** `geom` カラムに GIST インデックスを貼ること。

#### B. 大量データ生成と高速インサート

- **10万件**のランダムなデータを生成し、データベースに登録してください。
- **要件:** 1件ずつ `INSERT` するのではなく、`psycopg2` の `execute_values` や `copy_from` 等を使用して、**バルクインサート**を実装してください。
- インサートにかかった時間を計測し、表示してください。

#### C. 検索ロジック（PostGIS最適化）

- 特定の座標から半径 `N` メートル以内の店舗を検索する関数を作成します。
- **要件:** `ST_Expand` と `&&` 演算子（バウンディングボックス検索）を組み合わせて、インデックスを確実に活用するクエリを書くこと。
- ヒント：`WHERE geom && ST_Expand(center, distance) AND ST_Distance(...) < distance`

#### D. マルチスレッドによる負荷シミュレーション

- `ThreadPoolExecutor` を使用して、**「100個の異なる地点」**からの同時検索をシミュレーションしてください。
- **要件:**
  - 同時に実行する最大スレッド数を制御すること（例：`max_workers=10`）。
  - 100個のクエリがすべて完了するまでの総時間を計測すること。

#### E. パフォーマンス分析

- 各クエリの結果件数と、全体の平均処理時間を表示してください。

---

### 2. 方針

対応は以下の３つに分ける

- A. データベース設計
- B. 大量データ生成と高速インサート
- C~E. 検索ロジック（PostGIS最適化） / マルチスレッドによる負荷シミュレーション / パフォーマンス分析

---

### 3. 設計

#### 3-1. データベース設計

- CREATE TABLEでデータベースを作成
- テーブル名はstores
- NULLは許可しない
- カラムの条件
  - `id`: シリアル型（主キー）
  - `name`: 文字列（店舗名）
  - `category`: 文字列（カテゴリ：`restaurant`, `cafe`, `market`, `Bakery`, `Bar`, `C-store`）
  - `geom`: `GEOMETRY(Point, 4326)` 型
  - **必須:** `geom` カラムに GIST インデックスを貼ること。

```sql
CREATE TABLE stores (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    category VARCHAR(255) NOT NULL CHECK (category IN ('restaurant', 'cafe', 'market', 'Bakery', 'Bar', 'C-store')),
    geom GEOMETRY(Point, 4326) NOT NULL
);
CREATE INDEX idx_stores_geom ON stores USING GIST(geom);
```

- カテゴリを追加する場合

```sql
-- 1. 古いチェック制約を削除
ALTER TABLE stores DROP CONSTRAINT stores_category_check;
-- 2. 新しいカテゴリ(`Set-Meal-shop`)を追加した制約を再設定
ALTER TABLE stores ADD CONSTRAINT stores_category_check CHECK (category IN ('Restaurant', 'Cafe', 'Market', 'Bakery', 'Bar', 'C-store', 'Set-Meal-shop'));
```

- インデックスを削除する場合(INSERT前に削除した方が高速なため)

```sql
-- 1. インデックスの削除
DROP INDEX IF EXISTS idx_stores_geom;

-- 2. インデックスの追加と統計情報の更新
CREATE INDEX idx_stores_geom ON stores USING GIST(geom);
ANALYZE stores;
```

---

#### 3-2. 大量データ生成と高速インサート

##### 要件の理解

- **要件:** 1件ずつ `INSERT` するのではなく、`psycopg2` の `execute_values` や `copy_from` 等を使用して、**バルクインサート**を実装してください。
  - `python` の `psycopg2` モジュールを利用する形はNW通信の分時間がかかるので `INSERT INTO stores (id ,name, category, geom) SELECT ...略...;` の形にする
  - idはSELECTで取得し、その後にserialを更新
  - nameは店舗名のパーツを配列で定義してランダムで作成
    - 接頭辞リスト: ['ミント', 'ハッピー', 'サンライズ', 'ゴールデン', 'ラッキー', 'スペシャル', '気まぐれ', '毎日', '爽やか', 'everyday']
    - 接尾辞リスト: ['レストラン', 'カフェ', 'スーパー', 'ベーカリー', '居酒屋', 'コンビニ', '定食']
- インサートにかかった時間を計測し、表示してください。
  - DO文(`DO $$ END $$`)を使って時間を計測する

```sql
DO $$
DECLARE
    prefixes TEXT[] := ARRAY['ミント', 'ハッピー', 'サンライズ', 'ゴールデン', 'ラッキー', 'スペシャル', '気まぐれ', '毎日', '爽やか', 'everyday'];
    suffixes TEXT[] := ARRAY['レストラン', 'カフェ', 'スーパー', 'ベーカリー', '居酒屋', 'コンビニ'];
    categories TEXT[] := ARRAY['restaurant', 'cafe', 'market', 'Bakery', 'Bar', 'C-store'];
    start_time TIMESTAMP := clock_timestamp();

BEGIN
    INSERT INTO stores (id, name, category)
    SELECT
        s AS id,
        prefixes[floor(random() * 10 + 1)] || suffixes[suffix_idx] AS name,
        categories[suffix_idx] AS category
    FROM (
        SELECT
            s,
            floor(random() * 7 + 1)::int AS suffix_idx
        FROM generate_series(1,3) AS s
    );
    RAISE NOTICE 'actual time: %', clock_timestamp() - start_time;
END $$;
```
