# Demo Checkout Service

E-commerce checkout service with realistic fault injection for incident demonstration.

## 🎯 Purpose

Generates realistic application logs with injected faults to CloudWatch, simulating production incidents for the Autonomous Incident Commander to investigate.

## 🚀 Quick Start

### Prerequisites

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) package manager
- AWS CLI configured with credentials
- Terraform (for deployment)

### Setup

```bash
# Install dependencies with uv
uv sync

# Activate virtual environment
source .venv/bin/activate

# Test locally
python -m src.lambda_handler
```

### Deploy to AWS

```bash
# Package Lambda
bash scripts/package.sh

# Deploy with Terraform
cd terraform
terraform init
terraform plan
terraform apply
```

## 📦 Project Structure

```
demo-checkout-service/
├── src/
│   ├── lambda_handler.py       # Main Lambda function
│   ├── fault_injector.py       # Fault injection logic
│   └── config.py               # Configuration
├── tests/
│   ├── test_lambda_handler.py
│   └── test_fault_injection.py
├── terraform/
│   └── modules/
│       └── lambda/             # Lambda + CloudWatch setup
├── scripts/
│   ├── package.sh              # Package for deployment
│   └── trigger_traffic.py      # Traffic generator
├── pyproject.toml              # uv project config
├── .env.example                # Environment template
└── README.md
```

## 🎭 Fault Scenarios

1. **Normal** (80% success) - Baseline operation
2. **DB Pool Exhaustion** (50% errors) - Main demo scenario
3. **Memory Leak** (gradual degradation) - Performance pattern
4. **Cascading Failure** (70% errors) - Total system failure

Configure via `FAULT_SCENARIO` environment variable.

## 🧪 Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src

# Run specific test
uv run pytest tests/test_lambda_handler.py -v
```

## 📊 Usage

### Local Testing

```bash
# Test single invocation
uv run python -m src.lambda_handler

# Test with specific scenario
FAULT_SCENARIO=db_pool_exhaustion uv run python -m src.lambda_handler
```

### Traffic Generation

```bash
# Generate normal traffic (10 min)
uv run python scripts/trigger_traffic.py traffic --duration 10

# Trigger incident
uv run python scripts/trigger_traffic.py incident --scenario db_pool_exhaustion
```

## 🔧 Configuration

Copy `.env.example` to `.env`:

```bash
FAULT_SCENARIO=normal
LOG_LEVEL=INFO
AWS_REGION=us-east-1
FUNCTION_NAME=demo-checkout-service
```

## 📝 License

MIT
