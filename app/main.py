"""FastAPI service that serves the house price model.

Cloud-friendly features:
- Model is loaded from local disk, or from S3 if MODEL_S3_BUCKET is set.
- /health endpoint for load balancers and container health checks.
- Predictions are logged as JSON to stdout (shows up in CloudWatch / Cloud Logging).
- Optional: store predictions in DynamoDB if DYNAMODB_TABLE is set.
"""
import json
import logging
import os
import time
import uuid
from pathlib import Path

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("house-price")

MODEL_PATH = Path(os.getenv("MODEL_PATH", "model/model.joblib"))
METRICS_PATH = Path("model/metrics.json")
S3_BUCKET = os.getenv("MODEL_S3_BUCKET")
S3_KEY = os.getenv("MODEL_S3_KEY", "model.joblib")
DDB_TABLE = os.getenv("DYNAMODB_TABLE")


def load_model():
    if S3_BUCKET:
        import boto3
        MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
        boto3.client("s3").download_file(S3_BUCKET, S3_KEY, str(MODEL_PATH))
        log.info(json.dumps({"event": "model_downloaded", "bucket": S3_BUCKET}))
    return joblib.load(MODEL_PATH)


model = load_model()
metrics = json.loads(METRICS_PATH.read_text()) if METRICS_PATH.exists() else {}
ddb = None
if DDB_TABLE:
    import boto3
    ddb = boto3.resource("dynamodb").Table(DDB_TABLE)

app = FastAPI(title="House Price Prediction API", version="1.0")


class House(BaseModel):
    area_sqft: float = Field(..., gt=200, lt=20000)
    bedrooms: int = Field(..., ge=1, le=10)
    bathrooms: int = Field(..., ge=1, le=10)
    age_years: int = Field(..., ge=0, le=200)
    location: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/info")
def info():
    return {"metrics": metrics}


@app.post("/predict")
def predict(house: House):
    allowed = metrics.get("locations")
    if allowed and house.location not in allowed:
        raise HTTPException(422, f"location must be one of {allowed}")
    start = time.time()
    df = pd.DataFrame([house.model_dump()])
    price = float(model.predict(df)[0])
    record = {"id": str(uuid.uuid4()), "ts": int(time.time()),
              **house.model_dump(), "predicted_price": round(price, 2)}
    log.info(json.dumps({"event": "prediction",
                         "latency_ms": round((time.time() - start) * 1000, 1), **record}))
    if ddb:
        try:
            from decimal import Decimal
            ddb.put_item(Item=json.loads(json.dumps(record), parse_float=Decimal))
        except Exception as e:  # never fail a prediction because logging failed
            log.warning(json.dumps({"event": "ddb_error", "error": str(e)}))
    return {"predicted_price": round(price, 2)}


app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def index():
    return FileResponse("static/index.html")
