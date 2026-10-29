# Deployment Guide (AWS, free-tier friendly)

Pick ONE of the options. Option A is the easiest; B shows more cloud concepts.

## Option A: AWS App Runner (container, no servers to manage)

1. Install the AWS CLI and run `aws configure`.
2. Create a registry and push the image (replace `REGION` and `ACCOUNT_ID`):
   ```bash
   aws ecr create-repository --repository-name house-price --region REGION
   aws ecr get-login-password --region REGION | docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com
   docker build -t house-price .
   docker tag house-price:latest ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/house-price:latest
   docker push ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/house-price:latest
   ```
3. AWS Console -> App Runner -> Create service -> Container registry (Amazon ECR) ->
   pick the image -> port `8000` -> health check path `/health` -> Create.
4. Open the public URL App Runner gives you.

## Option B: EC2 virtual machine (shows IaaS)

1. Launch a `t2.micro`/`t3.micro` Ubuntu instance. Security group: allow inbound TCP 22 and 80.
2. SSH in, then:
   ```bash
   sudo apt update && sudo apt install -y docker.io git
   git clone <your-repo-url> && cd house-price-cloud
   sudo docker build -t house-price .
   sudo docker run -d -p 80:8000 --restart always house-price
   ```
3. Visit `http://<EC2-public-IP>`.

## Option C: Other clouds

- **Render / Railway**: connect the GitHub repo, choose Docker, deploy. The app reads `$PORT` automatically.
- **Google Cloud Run**: `gcloud run deploy house-price --source . --allow-unauthenticated`

## Optional upgrades (extra marks)

**S3 for the model**
```bash
aws s3 mb s3://YOUR-UNIQUE-BUCKET
aws s3 cp model/model.joblib s3://YOUR-UNIQUE-BUCKET/model.joblib
```
Set `MODEL_S3_BUCKET=YOUR-UNIQUE-BUCKET` on the service and give it an IAM role with `s3:GetObject`.

**DynamoDB for prediction history**
```bash
aws dynamodb create-table --table-name predictions \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH --billing-mode PAY_PER_REQUEST
```
Set `DYNAMODB_TABLE=predictions` and give the role `dynamodb:PutItem`.

**Monitoring**: every prediction is logged as JSON (with latency). In CloudWatch Logs, use
Logs Insights: `fields @timestamp, latency_ms, predicted_price | filter event="prediction"`.

**Auto-scaling**: App Runner scales automatically (set min/max instances in the service config).
For EC2, put an Application Load Balancer in front of an Auto Scaling Group.

**Load test (for your report)**: `pip install locust` or use `hey -n 500 -c 20 <url>/health`.

## Clean up to avoid charges
Delete the App Runner service / terminate the EC2 instance, then the ECR repo, S3 bucket and DynamoDB table.
