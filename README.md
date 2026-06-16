# Serverless Stock Dashboard

Serverless Stock Dashboard is an AWS serverless app that tracks a tech stock watchlist, finds the daily stock with the largest percent move, stores that winner in DynamoDB, and displays the stored history in a React dashboard.

## A. Live links

Frontend:
http://serverless-stock-dashboard-450374452948-us-east-1.s3-website-us-east-1.amazonaws.com

API:
https://o3k1sp6nhf.execute-api.us-east-1.amazonaws.com/prod/movers

## B. Prerequisites

Install these first.

```text
Docker Desktop
AWS CLI
Git
An AWS account
A Massive account and API key
```

This project uses Docker Compose, so you do not need to install Python packages or Node packages directly on your machine.

## C. Setup steps

### 1. Clone the repo

```bash
git clone https://github.com/Ephimoon/Serverless-Stock-Dashboard.git
cd Serverless-Stock-Dashboard
```

### 2. Get a Massive API key

Create a Massive account.

Open the Massive dashboard.

Find the API key section.

Copy your API key.

Do not paste the real key into GitHub or into any committed file.

### 3. Create the AWS Secrets Manager secret

This project expects the Massive API key to already exist in AWS Secrets Manager before deployment.

Use this AWS region.

```text
us-east-1
```

Use this secret name.

```text
stock-dashboard/api-key
```

In AWS Console, go to:

```text
AWS Console
Secrets Manager
Store a new secret
Other type of secret
Key/value
```

Add this key and value.

```text
STOCK_API_KEY = your Massive API key
```

Use this secret name.

```text
stock-dashboard/api-key
```

Finish creating the secret.

The ingestion Lambda reads this secret at runtime. The real API key is not committed to the repo.

### 4. Configure local AWS access

Check that the AWS CLI can access your account.

```bash
aws sts get-caller-identity
```

If that fails, configure AWS first.

```bash
aws configure
```

Use these values when prompted.

```text
AWS Access Key ID: your AWS access key
AWS Secret Access Key: your AWS secret access key
Default region name: us-east-1
Default output format: json
```

If you use a named AWS profile, use that same profile name in the `.env` file.

### 5. Create the local env file

Copy the example file.

```bash
cp .env.example .env
```

Use this format.

```text
STOCK_API_KEY=your_stock_api_key_here
TABLE_NAME=serverless-stock-dashboard-movers
AWS_REGION=us-east-1
AWS_PROFILE=default
SECRET_NAME=stock-dashboard/api-key
```

You can leave `STOCK_API_KEY` as `your_stock_api_key_here` if you already created the AWS Secrets Manager secret. The backend ignores that placeholder value and reads the real key from Secrets Manager.

The `.env` file is only for local development. It is ignored by Git.

### 6. Build and test with Docker

Build the containers.

```bash
docker compose build
```

Run backend tests.

```bash
docker compose run --rm backend-tests
```

Build the frontend.

```bash
docker compose run --rm frontend-build
```

Run CDK synth.

```bash
docker compose run --rm cdk
```

### 7. Deploy to AWS from your machine

For a fresh AWS account, the first deploy creates the API Gateway URL and S3 website URL. The frontend needs the API base URL, so after the first deploy, rebuild the frontend with the new API base URL and deploy again.

Bootstrap CDK one time for your AWS account and region.

```bash
docker compose run --rm cdk-bootstrap
```

Deploy the stack.

```bash
docker compose run --rm cdk-deploy
```

After deploy finishes, CDK prints outputs like this.

```text
ApiUrl
FrontendUrl
TableName
SecretName
AlertTopicArn
```

Save the `ApiUrl` and `FrontendUrl`.

The API URL will look like this.

```text
https://example.execute-api.us-east-1.amazonaws.com/prod/movers
```

The frontend needs the API base URL without `/movers`.

```text
https://example.execute-api.us-east-1.amazonaws.com/prod
```

Rebuild the frontend with your deployed API base URL.

```bash
docker compose run --rm \
  -e VITE_API_BASE_URL=https://example.execute-api.us-east-1.amazonaws.com/prod \
  frontend-build
```

Deploy again so the S3 frontend uses your API URL.

```bash
docker compose run --rm cdk-deploy
```

Open the `FrontendUrl` that CDK printed.

### 8. Run the frontend locally

Use your deployed API base URL.

```bash
docker compose run --rm \
  -p 5173:5173 \
  -e VITE_API_BASE_URL=https://example.execute-api.us-east-1.amazonaws.com/prod \
  frontend-build \
  sh -c "npm run dev -- --host 0.0.0.0"
```

Open this in the browser.

```text
http://localhost:5173
```

### 9. Test the deployed API with curl

Set your API base URL.

```bash
API_BASE_URL=https://example.execute-api.us-east-1.amazonaws.com/prod
```

Get the newest history page.

```bash
curl -i "$API_BASE_URL/movers?limit=7"
```

If the response has `next_cursor`, test the older page.

```bash
curl -i "$API_BASE_URL/movers?limit=7&cursor=PASTE_NEXT_CURSOR_HERE"
```

`PASTE_NEXT_CURSOR_HERE` means copy the exact `next_cursor` value from the first response.

You can manually trigger the ingestion Lambda if you want to test the daily scan right away.

```bash
aws lambda invoke \
  --function-name serverless-stock-dashboard-ingestion \
  --region us-east-1 \
  response.json
```

Read the Lambda response.

```bash
cat response.json
```

Then call the API again.

```bash
curl -i "$API_BASE_URL/movers?limit=7"
```

### 10. Configure GitHub Actions for production deploys

In GitHub, open the repository.

Go to:

```text
Settings
Secrets and variables
Actions
```

Add these repository secrets.

```text
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_REGION
```

Use this value for `AWS_REGION`.

```text
us-east-1
```

Then go to the Variables tab and add this repository variable.

```text
VITE_API_BASE_URL
```

Set it to your API base URL without `/movers`.

```text
https://example.execute-api.us-east-1.amazonaws.com/prod
```

When you push to `main`, GitHub Actions runs the production deploy.

```text
Backend tests
Frontend build
CDK synth
AWS deploy
```

Pull requests run the checks but do not deploy.

For a fresh AWS account, deploy locally first so you can get the API URL. Then add `VITE_API_BASE_URL` to GitHub and use GitHub Actions for future production deploys.


## D. Before pushing

Make sure `.env` is not tracked.

```bash
git ls-files .env
```

If it prints `.env`, remove it from Git tracking.

```bash
git rm --cached .env
```

Make sure the real Massive API key is not anywhere in the repo.

```bash
git grep "YOUR_REAL_KEY"
```

Replace `YOUR_REAL_KEY` with the actual key text before running the command.

## E. Project structure

```text
backend
  api
    Handles GET /movers
    Reads winner records from DynamoDB
    Supports limit and cursor pagination
    Returns clean JSON and response headers

  ingest
    Runs from the EventBridge schedule
    Gets the Massive API key from AWS Secrets Manager
    Chooses the market date to evaluate
    Calls Massive for each ticker in the watchlist
    Calculates percent change from open and close
    Stores the ticker with the largest absolute move in DynamoDB

  common
    Shared config, AWS clients, response helpers, secret loading, and stock mover logic

  tests
    Unit tests for API behavior, ingestion behavior, pagination, error handling, and response formatting

frontend
  src
    React TypeScript dashboard

  src/components
    Header, summary cards, leaderboard, timeline, table, trend chart, loading state, and error state

  src/services
    API client for GET /movers

  src/utils
    Date formatting, percent formatting, ticker scoring, and dashboard summary calculations

infrastructure
  AWS CDK stack
  DynamoDB table
  EventBridge schedule
  Ingestion Lambda
  API Lambda
  API Gateway
  S3 static website hosting
  Secrets Manager reference
  CloudWatch logs and alarms
  SNS alert topic

.github
  GitHub Actions workflow for tests, frontend build, CDK synth, and production deploy

docker-compose.yml
  Local commands for backend tests, frontend builds, CDK synth, and deploys

.env.example
  Example local environment variables without real secrets
```

## F. How the stock mover logic works

The ingestion Lambda does not blindly use the current UTC date. It chooses the market date based on New York market time because the stock market closes on Eastern time.

The date selection works like this:

```text
If today is a weekday and it is already after the safe market close cutoff in New York time, use today.
Otherwise, use the previous weekday.
If the selected date has no stock data because of a holiday or missing API data, try an earlier weekday.
```

Examples:

```text
Tuesday at 7 PM Eastern uses Tuesday.
Tuesday at 4 AM Eastern uses Monday.
Sunday uses Friday.
If Monday was a market holiday and the API has no data, the Lambda falls back to Friday.
```

After choosing the market date, the Lambda evaluates the watchlist.

```text
AAPL
MSFT
GOOGL
AMZN
TSLA
NVDA
```

For each ticker, the Lambda calls Massive and reads the open and close price for the selected market date. It calculates percent change with this formula:

```text
((close price minus open price) divided by open price) times 100
```

The Lambda compares the absolute value of each percent change. This means a large loss can win the day the same way a large gain can win the day. For example, negative 7 percent beats positive 3 percent because the absolute move is larger.

The Lambda uses partial success handling. If one ticker fails because the stock API has a temporary issue or rate limit, the Lambda logs that ticker failure and keeps evaluating the other tickers for the same market date. The run only fails if none of the watchlist tickers return valid data.

The daily winner stored in DynamoDB includes:

```text
Date
Ticker symbol
Percent change
Closing price
Direction
Created timestamp
```

The API Lambda reads these DynamoDB records and returns them through `GET /movers`. The endpoint supports `limit` and `cursor`, so the frontend can show the newest seven records first and then load older history pages without requesting every record at once.


## G. Tradeoffs

I used S3 static website hosting for the frontend because it matches the project requirement and keeps the deployment simple. The tradeoff is that the S3 website URL uses HTTP. I considered adding CloudFront for HTTPS, but I left it out because the assignment allowed S3 static website hosting and I wanted to keep the project focused on the serverless pipeline.

I did not enable API Gateway caching because it can add cost. Instead, the API returns cache headers and supports cursor pagination. This gives the frontend a clean way to move through older DynamoDB records without loading everything at once.

For the ingestion Lambda, I chose a partial success approach. The Lambda evaluates the watchlist for the same market date and stores the best result from the tickers that return valid data. If one ticker fails or the stock API has a temporary issue, the whole run does not fail unless none of the tickers work. This made the pipeline more reliable during testing while still recording a real daily winner.

The stock API key is stored in AWS Secrets Manager instead of being committed to the repo or passed through the frontend. This adds one setup step for anyone deploying the project in a new AWS account, but it keeps the key out of GitHub and lets the Lambda read it securely at runtime.

For GitHub Actions, I used GitHub repository secrets for the AWS credentials because it was the simplest setup for a take home project. In a production system, I would prefer GitHub OIDC so the workflow can assume an AWS role without storing long lived AWS keys in GitHub.

The stack creates CloudWatch alarms and an SNS topic for alerts. I kept the email subscription optional because an email subscriber has to be confirmed by the person deploying the project. The alarms and topic are still part of the infrastructure, so a new owner can attach their own email or alerting target after deployment.

A fresh AWS account may need two deploys for the frontend. The first deploy creates the API Gateway URL. After that, the API base URL can be added to the frontend build configuration and the S3 frontend can be redeployed with the correct API connection.
