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
```

- カテゴリを追加する場合

```
-- 1. 古いチェック制約を削除
ALTER TABLE stores DROP CONSTRAINT store_category_check;
-- 2. 新しいカテゴリ(`Set-Meal-shop`)を追加した制約を再設定
ALTER TABLE sotre ADD CONSTRAINT sotres_category_check CHECK (category IN ('Restaurant', 'Cafe', 'Market', 'Bakery', 'Bar', 'C-store', 'Set-Meal-shop'));
```
