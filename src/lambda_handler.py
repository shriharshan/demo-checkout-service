"""
Demo E-commerce Checkout Service - Lambda Function

Simulates a realistic checkout service with fault injection for incident demonstration.
Logs structured JSON to CloudWatch for analysis by Incident Commander.
"""

from aws_lambda_powertools import Logger, Tracer, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.typing import LambdaContext
import random
import time
import os
import json
from datetime import datetime
from typing import Dict, Any

# Initialize AWS Lambda Powertools
logger = Logger(service="checkout-service")
tracer = Tracer(service="checkout-service")
metrics = Metrics(namespace="DemoApp", service="checkout-service")


class FaultInjector:
    """Manages fault injection scenarios"""

    # Fault injection scenarios
    FAULT_SCENARIOS = {
        "normal": {
            "db_timeout_rate": 0.05,
            "slow_query_rate": 0.10,
            "exception_rate": 0.05,
            "db_pool_size": 10,
            "concurrent_calls": 1,
            "query_duration_ms": 150,
            "timeout_ms": 5000,
        },
        "db_pool_exhaustion": {
            "db_timeout_rate": 0.50,
            "slow_query_rate": 0.30,
            "exception_rate": 0.00,
            "db_pool_size": 3,
            "concurrent_calls": 5,
            "query_duration_ms": 150,
            "timeout_ms": 5000,
        },
        "deployment_config_bug": {
            # Simulates bad config deployed 15 mins ago
            # Symptoms: 40% timeout rate + 2000ms latency spikes
            "db_timeout_rate": 0.40,
            "slow_query_rate": 0.40,
            "exception_rate": 0.10,
            "db_pool_size": 5,  # Config changed from 10 → 5 (bad!)
            "concurrent_calls": 8,  # Load increased but pool decreased
            "query_duration_ms": 2000,  # Latency spike to 2000ms
            "timeout_ms": 3000,  # Aggressive timeout
            "deployment_time_offset_mins": 15,  # Triggered 15 mins after deploy
        },
        "memory_leak": {
            "db_timeout_rate": 0.10,
            "slow_query_rate": 0.20,
            "exception_rate": 0.15,
            "db_pool_size": 10,
            "concurrent_calls": 1,
            "query_duration_ms": 300,
            "timeout_ms": 5000,
        },
        "cascading_failure": {
            "db_timeout_rate": 0.70,
            "slow_query_rate": 0.20,
            "exception_rate": 0.10,
            "db_pool_size": 2,
            "concurrent_calls": 10,
            "query_duration_ms": 500,
            "timeout_ms": 2000,
        },
    }

    @staticmethod
    def get_active_scenario() -> str:
        """Get current fault scenario from environment"""
        return os.getenv("FAULT_SCENARIO", "normal")

    @staticmethod
    def get_fault_config() -> Dict[str, float]:
        """Get fault injection configuration for active scenario"""
        scenario = FaultInjector.get_active_scenario()
        config = FaultInjector.FAULT_SCENARIOS.get(
            scenario, FaultInjector.FAULT_SCENARIOS["normal"]
        )

        # For memory leak, calculate dynamic latency
        if scenario == "memory_leak":
            invocation_count = FaultInjector._get_invocation_count()
            degradation_factor = min(invocation_count / 100, 5.0)
            config["additional_latency_ms"] = int(100 * degradation_factor)

        return config

    @staticmethod
    def _get_invocation_count() -> int:
        """Track invocation count for memory leak simulation"""
        count_file = "/tmp/invocation_count.txt"
        count = 0

        try:
            if os.path.exists(count_file):
                with open(count_file) as f:
                    count = int(f.read().strip())
        except Exception:
            pass

        count += 1

        try:
            with open(count_file, "w") as f:
                f.write(str(count))
        except Exception:
            pass

        return count


@tracer.capture_method
def simulate_database_query(order_id: str, user_id: str) -> Dict[str, Any]:
    """
    Simulates database query with realistic fault injection

    Args:
        order_id: Order identifier
        user_id: User identifier

    Returns:
        Query result or raises exception
    """
    fault_config = FaultInjector.get_fault_config()
    scenario = FaultInjector.get_active_scenario()

    # Get DB pool configuration (needed for timeout error reporting)
    db_pool_size = fault_config.get("db_pool_size", 10)
    concurrent_calls = fault_config.get("concurrent_calls", 1)
    base_query_duration = fault_config.get("query_duration_ms", 150)
    timeout_threshold = fault_config.get("timeout_ms", 5000)

    # Determine fault type based on probabilities
    fault_roll = random.random()

    # Inject database timeout
    if fault_roll < fault_config.get("db_timeout_rate", 0):
        query_duration = random.randint(4500, 5500)
        # Simulate waiting for connection from pool
        query_duration = random.randint(4500, 5500)  # Original query duration for timeout
        actual_wait_time = timeout_threshold if concurrent_calls > db_pool_size else query_duration

        # Check if this is deployment-related
        deployment_info = {}
        if fault_config.get("deployment_time_offset_mins"):
            from datetime import datetime, timedelta

            deploy_time = datetime.now() - timedelta(
                minutes=fault_config["deployment_time_offset_mins"]
            )
            deployment_info = {
                "possibly_deployment_related": True,
                "recent_deployment_time": deploy_time.isoformat(),
                "minutes_since_deployment": fault_config["deployment_time_offset_mins"],
            }

        logger.error(
            "Database connection timeout - pool exhausted",
            extra={
                "error_type": "TimeoutError",
                "database": "orders_db",
                "query_duration_ms": query_duration,
                "wait_time_ms": actual_wait_time,
                "db_pool_size": db_pool_size,
                "concurrent_calls": concurrent_calls,
                "pool_available": db_pool_size - concurrent_calls,
                "order_id": order_id,
                "user_id": user_id,
                "fault_scenario": scenario,
                **deployment_info,
            },
        )
        metrics.add_metric(name="db_timeout", unit=MetricUnit.Count, value=1)
        metrics.add_metric(name="db_pool_exhausted", unit=MetricUnit.Count, value=1)
        raise TimeoutError(
            f"Database connection timeout after {actual_wait_time}ms waiting for connection. "
            f"Pool size: {db_pool_size}, Concurrent requests: {concurrent_calls}"
        )

    # Inject slow query
    elif fault_roll < fault_config.get("db_timeout_rate", 0) + fault_config.get(
        "slow_query_rate", 0
    ):
        # Simulate query duration (with some variance)
        query_duration = random.randint(
            int(base_query_duration * 0.8), int(base_query_duration * 1.2)
        )
        time.sleep(query_duration / 1000)

        # Check if latency is extremely high (2000ms+)
        is_latency_spike = query_duration >= 2000

        # Check deployment correlation
        deployment_info = {}
        if fault_config.get("deployment_time_offset_mins"):
            from datetime import datetime, timedelta

            deploy_time = datetime.now() - timedelta(
                minutes=fault_config["deployment_time_offset_mins"]
            )
            deployment_info = {
                "possibly_deployment_related": True,
                "recent_deployment_time": deploy_time.isoformat(),
                "minutes_since_deployment": fault_config["deployment_time_offset_mins"],
            }

        log_msg = (
            "LATENCY SPIKE - Query took 2000ms+"
            if is_latency_spike
            else "Slow database query detected"
        )

        if is_latency_spike:
            logger.error(
                log_msg,
                extra={
                    "order_id": order_id,
                    "user_id": user_id,
                    "query_duration_ms": query_duration,
                    "latency_threshold_exceeded": "2000ms",
                    "query_type": "SELECT",
                    "table": "orders",
                    "fault_scenario": scenario,
                    **deployment_info,
                },
            )
        else:
            logger.warning(
                log_msg,
                extra={
                    "order_id": order_id,
                    "user_id": user_id,
                    "query_duration_ms": query_duration,
                    "query_type": "SELECT",
                    "table": "orders",
                    "fault_scenario": scenario,
                },
            )

        metrics.add_metric(name="SlowQueries", unit=MetricUnit.Count, value=1)
        return {"status": "success", "latency": "high", "duration_ms": query_duration}

    # Inject unhandled exception
    elif fault_roll < (
        fault_config.get("db_timeout_rate", 0)
        + fault_config.get("slow_query_rate", 0)
        + fault_config.get("exception_rate", 0)
    ):
        logger.error(
            "Unhandled exception in order processing",
            extra={
                "order_id": order_id,
                "user_id": user_id,
                "error_type": "NullPointerException",
                "stack_trace": "at OrderProcessor.validate() line 142",
                "fault_scenario": scenario,
            },
        )

        metrics.add_metric(name="UnhandledExceptions", unit=MetricUnit.Count, value=1)
        raise Exception("NullPointerException: order.paymentMethod is null")

    # Normal operation
    else:
        normal_duration = random.randint(80, 150)

        # Add memory leak latency if applicable
        additional_latency = fault_config.get("additional_latency_ms", 0)
        if additional_latency > 0:
            time.sleep(additional_latency / 1000)
            normal_duration += additional_latency

        time.sleep(normal_duration / 1000)

        logger.info(
            "Order processed successfully",
            extra={
                "order_id": order_id,
                "user_id": user_id,
                "processing_time_ms": normal_duration,
                "payment_method": "credit_card",
                "total_amount": round(random.uniform(20.0, 500.0), 2),
            },
        )

        metrics.add_metric(name="SuccessfulOrders", unit=MetricUnit.Count, value=1)
        return {"status": "success", "duration_ms": normal_duration}


@logger.inject_lambda_context(log_event=True)
@tracer.capture_lambda_handler
@metrics.log_metrics(capture_cold_start_metric=True)
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler for checkout requests

    Processes checkout requests with realistic fault injection.
    Logs structured data to CloudWatch for incident analysis.
    """

    # Extract order details
    order_id = event.get("order_id", f"ORD-{context.request_id[:8].upper()}")
    user_id = event.get("user_id", f"USER-{random.randint(1000, 9999)}")

    # Log scenario info
    scenario = FaultInjector.get_active_scenario()
    logger.info(
        "Processing checkout request",
        extra={
            "order_id": order_id,
            "user_id": user_id,
            "request_id": context.request_id,
            "fault_scenario": scenario,
            "function_version": context.function_version,
        },
    )

    try:
        # Simulate database operation
        result = simulate_database_query(order_id, user_id)

        # Record success metric
        metrics.add_metric(name="CheckoutRequests", unit=MetricUnit.Count, value=1)
        metrics.add_metric(
            name="ProcessingTime", unit=MetricUnit.Milliseconds, value=result.get("duration_ms", 0)
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                {"order_id": order_id, "status": "completed", "message": "Checkout successful"}
            ),
        }

    except TimeoutError as e:
        logger.exception(
            "Checkout failed due to timeout",
            extra={"order_id": order_id, "user_id": user_id, "error_type": "TimeoutError"},
        )

        metrics.add_metric(name="CheckoutFailures", unit=MetricUnit.Count, value=1)

        return {
            "statusCode": 504,
            "body": json.dumps(
                {"error": "Gateway Timeout", "message": str(e), "order_id": order_id}
            ),
        }

    except Exception as e:
        logger.exception(
            "Checkout failed with unexpected error",
            extra={"order_id": order_id, "user_id": user_id, "error_type": type(e).__name__},
        )

        metrics.add_metric(name="CheckoutFailures", unit=MetricUnit.Count, value=1)

        return {
            "statusCode": 500,
            "body": json.dumps(
                {"error": "Internal Server Error", "message": str(e), "order_id": order_id}
            ),
        }


# For local testing
if __name__ == "__main__":

    class MockContext:
        request_id = "local-test-123"
        function_version = "$LATEST"
        invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:demo-checkout-service"
        )
        memory_limit_in_mb = 512
        function_name = "demo-checkout-service"

    test_event = {"order_id": "TEST-001", "user_id": "USER-9999"}

    result = handler(test_event, MockContext())
    print(json.dumps(result, indent=2))
