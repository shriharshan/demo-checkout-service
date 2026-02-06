# Local Testing Guide - Demo Checkout Service

## 🧪 Quick Start: Test Locally

### 1. Setup Environment

```bash
cd demo-checkout-service

# Install dependencies
uv sync

# Activate virtual environment
source .venv/bin/activate
```

### 2. Run Local Tests

**Option A: Automated Test Script** (Recommended)

```bash
# Test multiple scenarios automatically
uv run python scripts/test_local.py
```

This will:
- Run 10 requests with "normal" scenario (expected: ~80% success)
- Run 10 requests with "db_pool_exhaustion" scenario (expected: ~50% timeout)
- Show structured JSON logs for each request
- Display success/failure summary

**Option B: Manual Single Invocation**

```bash
# Set fault scenario (optional, defaults to "normal")
export FAULT_SCENARIO=db_pool_exhaustion

# Run the Lambda handler directly
uv run python src/lambda_handler.py
```

---

## 🎯 Available Fault Scenarios

Set via `FAULT_SCENARIO` environment variable:

### 1. `normal` (Default)
```bash
export FAULT_SCENARIO=normal
uv run python src/lambda_handler.py
```
- 80% success rate
- 5% DB timeouts
- 10% slow queries
- Realistic baseline behavior

### 2. `db_pool_exhaustion` (Primary Demo Scenario)
```bash
export FAULT_SCENARIO=db_pool_exhaustion
uv run python src/lambda_handler.py
```
- **50% timeout rate** 
- DB pool: 3 connections
- Concurrent calls: 5
- **Root Cause:** Pool exhaustion (5 calls > 3 connections)
- Query duration: 150ms
- Timeout after: 5000ms

### 3. `memory_leak`
```bash
export FAULT_SCENARIO=memory_leak
uv run python src/lambda_handler.py
```
- Gradual performance degradation
- Latency increases with each invocation
- Simulates memory pressure

### 4. `cascading_failure`
```bash
export FAULT_SCENARIO=cascading_failure
uv run python src/lambda_handler.py
```
- 70% error rate
- Simulates complete system failure

---

## 📊 Understanding the Logs

The Lambda handler uses **AWS Lambda Powertools** for structured JSON logging.

### Example: Normal Request (Success)
```json
{
  "level": "INFO",
  "location": "simulate_database_query:187",
  "message": "Order processed successfully",
  "timestamp": "2026-02-06 12:40:25,123",
  "service": "checkout-service",
  "order_id": "ORD-001",
  "user_id": "USER-1000",
  "processing_time_ms": 120,
  "payment_method": "credit_card",
  "total_amount": 145.67
}
```

### Example: DB Pool Exhaustion (Timeout)
```json
{
  "level": "ERROR",
  "location": "simulate_database_query:127",
  "message": "Database connection timeout - pool exhausted",
  "timestamp": "2026-02-06 12:40:30,456",
  "service": "checkout-service",
  "error_type": "TimeoutError",
  "database": "orders_db",
  "query_duration_ms": 4800,
  "wait_time_ms": 5000,
  "db_pool_size": 3,
  "concurrent_calls": 5,
  "pool_available": -2,  // 🔴 2 requests waiting for connection!
  "order_id": "ORD-DB_POOL_EXHAUSTION-003",
  "user_id": "USER-1002",
  "fault_scenario": "db_pool_exhaustion"
}
```

**Key Fields for RCA:**
- `db_pool_size`: 3 (max connections)
- `concurrent_calls`: 5 (app tried 5 calls)
- `pool_available`: -2 (2 requests blocked!)
- `wait_time_ms`: 5000 (timeout threshold)

---

## 🔍 Custom Testing

### Test Specific Order ID

```python
# Edit src/lambda_handler.py main block or create your own script

from src.lambda_handler import handler
import os
import json

class MockContext:
    request_id = "custom-test-001"
    function_version = "$LATEST"

# Set scenario
os.environ["FAULT_SCENARIO"] = "db_pool_exhaustion"

# Custom event
event = {
    "order_id": "MY-CUSTOM-ORDER-123",
    "user_id": "USER-9999"
}

result = handler(event, MockContext())
print(json.dumps(result, indent=2))
```

### Simulate High Load

```bash
# Run 100 requests with DB pool exhaustion
for i in {1..100}; do
  FAULT_SCENARIO=db_pool_exhaustion uv run python src/lambda_handler.py
done | grep -E "(SUCCESS|TIMEOUT|ERROR)"
```

---

## 📈 Expected Results by Scenario

| Scenario | Success Rate | Timeout Rate | Error Rate |
|----------|-------------|--------------|------------|
| `normal` | ~80% | ~5% | ~15% |
| `db_pool_exhaustion` | ~18% | **~50%** | ~32% |
| `memory_leak` | Degrades over time | Low | Increases |
| `cascading_failure` | 0% | ~70% | ~30% |

---

## 🚀 Next Steps: Deploy to AWS

Once you've tested locally and understand the logs:

```bash
# Package for Lambda
bash scripts/package.sh

# Deploy with Terraform
cd terraform
terraform init
terraform apply
```

Then use `scripts/trigger_traffic.py` to generate real CloudWatch logs for the Incident Commander to analyze.

---

## 💡 Tips

1. **Grep for errors:**
   ```bash
   uv run python scripts/test_local.py 2>&1 | grep -A5 "ERROR"
   ```

2. **Count timeouts:**
   ```bash
   uv run python scripts/test_local.py 2>&1 | grep -c "TimeoutError"
   ```

3. **Extract JSON logs only:**
   ```bash
   uv run python scripts/test_local.py 2>&1 | grep "^{" | jq .
   ```

4. **Test with different iterations:**
   ```python
   # Modify scripts/test_local.py:
   scenarios = [
       ("db_pool_exhaustion", 50),  # 50 requests instead of 10
   ]
   ```

---

**Ready to test!** Run `uv run python scripts/test_local.py` to see the demo app in action locally.
