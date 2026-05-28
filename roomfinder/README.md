# 福岡市「最適住まい探し」検索エンジン (PostGIS版)

福岡市内で、駅からの距離だけでなく「周辺施設数」や「ハザードマップ」を考慮した高度な物件探しができるシステムを構築します。

## 開発フェーズ

- [ ] Phase 1: データ収集・DB構築（←今ここ）
- [ ] Phase 2: FastAPIによるバックエンド構築
- [ ] Phase 3: 空間クエリ（API）の実装
- [ ] Phase 4: 可視化フロントエンドの作成

## 技術スタック

- **DB**: PostgreSQL / PostGIS
- **Backend**: Python (FastAPI, GeoPandas, SQLAlchemy)
- **Infra**: Docker
- **Data**: 国土数値情報, OpenStreetMap
