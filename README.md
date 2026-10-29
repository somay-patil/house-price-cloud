# House Price Prediction on the Cloud

A machine learning model (Random Forest) that predicts house prices, packaged as a
Docker container and served through a FastAPI REST API with a web form.

## Architecture

```
User browser --> Cloud container service (App Runner / EC2 / Cloud Run)
                      |  FastAPI + model
                      |-- loads model from S3 (optional)
                      |-- stores predictions in DynamoDB (optional)
                      '-- logs to CloudWatch
GitHub --> GitHub Actions (build + smoke test) --> ECR image registry
```

## Run locally

```bash
pip install -r requirements.txt
python train.py                      # creates model/model.joblib
uvicorn app.main:app --reload        # open http://localhost:8000
```

## Run with Docker

```bash
docker build -t house-price .
docker run -p 8000:8000 house-price
```

## API

| Method | Path       | Purpose                       |
|--------|------------|-------------------------------|
| GET    | `/`        | Web form                      |
| GET    | `/health`  | Health check for load balancers |
| GET    | `/info`    | Model metrics and locations   |
| POST   | `/predict` | Returns `predicted_price`     |

```bash
curl -X POST http://localhost:8000/predict -H "Content-Type: application/json" \
  -d '{"area_sqft":1800,"bedrooms":3,"bathrooms":2,"age_years":10,"location":"Suburb"}'
```

## Use YOUR dataset from the ML project

Put your CSV at `data/house_prices.csv` and edit `NUM`/`CAT` (column names) at the top of
`train.py` and the `House` fields in `app/main.py`. Re-run `python train.py`.
The bundled data is synthetic so the project works out of the box.

## Environment variables

| Variable          | Meaning                                         |
|-------------------|-------------------------------------------------|
| `MODEL_S3_BUCKET` | If set, the model is downloaded from this S3 bucket on startup |
| `MODEL_S3_KEY`    | Object key (default `model.joblib`)             |
| `DYNAMODB_TABLE`  | If set, every prediction is saved to this table (partition key `id`, String) |

See `DEPLOY.md` for cloud deployment steps.
