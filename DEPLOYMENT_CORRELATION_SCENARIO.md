# Deployment Correlation Test Scenario

## Scenario: Configuration Bug Introduced by Deployment

### Background Story
At 12:00 PM, a developer deployed a "performance optimization" that changed the database connection pool configuration:
- **Before:** `db_pool_size = 10`, `max_concurrent = 5`
- **After:** `db_pool_size = 5`, `max_concurrent = 8` ❌ **BAD CONFIG!**

The deployment succeeded, but **15 minutes later** (12:15 PM), users started experiencing:
- 40% timeout rate
- Latency spikes to 2000ms
- Connection pool exhaustion

---

## How to Simulate

### 1. Trigger the Fault Scenario

```bash
cd demo-checkout-service

# Set fault scenario to deployment_config_bug
export FAULT_SCENARIO=deployment_config_bug

# Run local test
uv run python scripts/test_local.py
```

### 2. Expected Logs

You should see errors like:

```json
{
  "level": "ERROR",
  "message": "Database connection timeout - pool exhausted",
  "db_pool_size": 5,
  "concurrent_calls": 8,
  "pool_available": -3,
  "possibly_deployment_related": true,
  "recent_deployment_time": "2026-02-06T11:45:00",
  "minutes_since_deployment": 15
}
```

```json
{
  "level": "ERROR",
  "message": "LATENCY SPIKE - Query took 2000ms+",
  "query_duration_ms": 2100,
  "latency_threshold_exceeded": "2000ms",
  "possibly_deployment_related": true,
  "minutes_since_deployment": 15
}
```

---

## What the Incident Commander Should Detect

### Logs Agent Findings:
- ✅ High error rate (40% timeouts)
- ✅ Pattern: "pool_available" is negative (-3)
- ✅ Correlation: Errors started ~15 mins ago
- ✅ Common field: `possibly_deployment_related: true`

### Metrics Agent Findings:
- ✅ P99 latency spiked to 2000ms
- ✅ Error rate jumped from 5% → 40%
- ✅ Spike started at 12:15 PM

### Deploy Agent Findings:
- ✅ Deployment at 12:00 PM (CloudTrail event)
- ✅ 15-minute correlation window matches
- ✅ Configuration change detected: `db_pool_size` modified

### Commander's RCA Report:

```markdown
## Root Cause
Configuration bug introduced in deployment at 12:00 PM.

## Evidence
1. Database pool size reduced from 10 → 5
2. Concurrent calls increased to 8
3. 40% timeout rate started exactly 15 minutes after deployment
4. Latency spiked to 2000ms (13x normal)

## Recommended Action
**ROLLBACK** deployment from 12:00 PM and restore `db_pool_size = 10`.

## Confidence: 95%
Strong temporal correlation + configuration evidence.
```

---

## Test Flow

```bash
# 1. Deploy demo-checkout-service with bad config
terraform apply -var="fault_scenario=deployment_config_bug"

# 2. Simulate deployment event (CloudTrail)
aws cloudtrail put-insight-selectors \
  --trail-name demo-trail \
  --event-selectors ReadWriteType=WriteOnly,IncludeManagementEvents=true

# 3. Generate traffic (simulates 15 mins of load)
for i in {1..50}; do
  curl -X POST $DEMO_URL -d '{"order_id": "TEST-'$i'"}'
  sleep 1
done

# 4. Invoke Incident Commander
curl -X POST $COMMANDER_URL \
  -d '{"alert": {"service": "demo-checkout-service", "triggered_at": "2026-02-06T12:15:00Z"}}'

# 5. Check RCA report
# Should mention deployment correlation + config bug
```

---

## Key Indicators in Logs

| Field | Normal | Config Bug | Significance |
|-------|--------|------------|--------------|
| `db_pool_size` | 10 | **5** ⚠️ | Reduced capacity |
| `concurrent_calls` | 1-3 | **8** ⚠️ | Higher load |
| `pool_available` | 7-9 | **-3** ❌ | Exhausted! |
| `query_duration_ms` | 150 | **2000** ⚠️ | 13x slower |
| `minutes_since_deployment` | N/A | **15** 🔍 | Correlation! |

---

## Success Criteria

Incident Commander should:
1. ✅ Detect deployment timing (15 mins correlation)
2. ✅ Identify config change as root cause
3. ✅ Recommend rollback action
4. ✅ Show high confidence (>90%)
5. ✅ Cite multiple evidence sources (logs + metrics + deploy)

This proves the system can solve **latent configuration bugs** - the hardest type of incident to diagnose! 🚀
