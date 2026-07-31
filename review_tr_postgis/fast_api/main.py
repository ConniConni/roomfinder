# uvicorn main:app --reload でサーバ起動（--reloadオプションで自動で再起動）
# /docs で自動生成されたswaggerドキュメントを確認できる
# /redoc でhtmlベースのドキュメントページも生成される

from fastapi import FastAPI

# fastapiをインスタンス化しそこに設定を加えていく
app = FastAPI()


# httpメソッドで"/"にgetでアクセスがあったら処理を行う
@app.get(
    "/countries/{country_name}"
)  # "/":パスオペレーション パスパラメータで動的な変数を組み込める
async def country(country_name: str):
    return {"country_name": country_name}
