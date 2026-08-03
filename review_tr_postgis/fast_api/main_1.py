import csv
from pathlib import Path
from fastapi import FastAPI
from pydantic import BaseModel

csv_file = Path(__file__).parent.parent / "result" / "search_results.csv"
print(csv_file)
app = FastAPI()


@app.get("/result")
async def get_search_result():
    with open(csv_file, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        for row in reader:
            first_row = row
            break
    return {"message": first_row}
