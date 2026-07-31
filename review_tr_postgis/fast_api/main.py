# uvicorn main:app --reload でサーバ起動（--reloadオプションで自動で再起動）
# /docs で自動生成されたswaggerドキュメントを確認できる
# /redoc でhtmlベースのドキュメントページも生成される

from typing import Optional, List
from fastapi import FastAPI
from pydantic import BaseModel


class ShopInfo(BaseModel):
    name: str
    location: str


class Item(BaseModel):
    name: str
    description: Optional[str] = None
    price: int
    tax: Optional[float] = None


class Data(BaseModel):
    shop_info: ShopInfo
    items: List[Item]


# fastapiをインスタンス化しそこに設定を加えていく
app = FastAPI()


@app.post("/")
async def create_item(data: Data):
    item_strings = [
        f"{item.name}は税込{int(item.price * (item.tax if item.tax is not None else 1.0))}円"
        for item in data.items
    ]
    message_text = ", ".join(item_strings)
    return {"message": f"店舗名:{data.shop_info.name} {message_text}"}


# # httpメソッドで"/"にgetでアクセスがあったら処理を行う
# @app.get(
#     "/countries/{country_name}"
# )  # "/":パスオペレーション パスパラメータで動的な変数を組み込める
# async def country(country_name: str):
#     return {"country_name": country_name}


# # /countries/?country_name=america&country_no=2でアクセスするとクエリパラメータの内容を表示する
# @app.get("/countries/")  # パスパラメータにない引数を使うとクエリパラメータとなる
# async def country(country_name: str = "japan", country_no: int = 1):
#     return {"country_name": country_name, "country_no": country_no}


# # パスパラメータとクエリパラメータの組み合わせ /countries/america?city_name=boston
# @app.get(
#     "/countries/{country_name}"
# )  # パスパラメータにない引数を使うとクエリパラメータとなる
# async def country(country_name: str = "japan", city_name: str = "tokyo"):
#     return {"country_name": country_name, "city_name": city_name}


# # Optional[] = Noneを使うことで必須ではない必須ではないオプションパラメータを用意する
# @app.get("/countries/")  # パスパラメータにない引数を使うとクエリパラメータとなる
# async def country(country_name: Optional[str] = None, country_no: Optional[int] = None):
#     return {"country_name": country_name, "country_no": country_no}
