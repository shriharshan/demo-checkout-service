"""
Additional error injection functions for diverse fault scenarios

This module provides various error types beyond database issues to demonstrate
comprehensive error handling and RCA capabilities.
"""

from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
import random

logger = Logger()
metrics = Metrics()


def inject_payment_api_error(order_id: str, user_id: str, scenario: str):
    """Simulate payment gateway API failure"""
    logger.error(
        "Payment gateway API call failed",
        extra={
            "error_type": "ExternalAPIError",
            "service": "payment-gateway",
            "status_code": 503,
            "order_id": order_id,
            "user_id": user_id,
            "retry_attempts": 3,
            "fault_scenario": scenario,
            "error_message": "Service Unavailable - Payment processor down",
        },
    )
    metrics.add_metric(name="APIErrors", unit=MetricUnit.Count, value=1)
    raise Exception("Payment gateway unavailable - Service temporarily down")


def inject_validation_error(order_id: str, user_id: str, scenario: str):
    """Simulate input validation failure"""
    invalid_fields = ["total_amount", "customer_email", "shipping_address"]
    field = random.choice(invalid_fields)

    logger.error(
        "Order validation failed",
        extra={
            "error_type": "ValidationError",
            "field": field,
            "violation": "invalid_format" if field != "total_amount" else "negative_value",
            "order_id": order_id,
            "user_id": user_id,
            "fault_scenario": scenario,
        },
    )
    metrics.add_metric(name="ValidationErrors", unit=MetricUnit.Count, value=1)
    raise ValueError(f"Validation failed: {field} has invalid value")


def inject_memory_error(order_id: str, user_id: str, scenario: str):
    """Simulate memory exhaustion"""
    logger.error(
        "Memory allocation failed",
        extra={
            "error_type": "MemoryError",
            "requested_bytes": 524288000,  # 500MB
            "available_bytes": 104857600,  # 100MB
            "order_id": order_id,
            "user_id": user_id,
            "fault_scenario": scenario,
            "context": "Processing large batch order with 10000+ items",
        },
    )
    metrics.add_metric(name="MemoryErrors", unit=MetricUnit.Count, value=1)
    raise MemoryError("Cannot allocate memory for large order processing")


def inject_external_api_timeout(order_id: str, user_id: str, scenario: str):
    """Simulate external service timeout"""
    services = ["inventory-api", "shipping-calculator", "tax-service"]
    service = random.choice(services)

    logger.error(
        f"{service} timeout",
        extra={
            "error_type": "ExternalServiceTimeout",
            "service": service,
            "timeout_ms": 10000,
            "order_id": order_id,
            "user_id": user_id,
            "fault_scenario": scenario,
            "endpoint": f"https://{service}.internal/api/v1/check",
        },
    )
    metrics.add_metric(name="ExternalTimeouts", unit=MetricUnit.Count, value=1)
    raise TimeoutError(f"{service} did not respond within timeout period")


def get_cumulative_error_probabilities(fault_config: dict) -> dict:
    """Calculate cumulative probabilities for error injection"""
    cumulative = 0.0
    thresholds = {}

    # Order matters - earlier checks have priority
    error_types = [
        "db_timeout_rate",
        "slow_query_rate",
        "api_error_rate",
        "validation_error_rate",
        "memory_error_rate",
        "external_api_error_rate",
        "exception_rate",
    ]

    for error_type in error_types:
        cumulative += fault_config.get(error_type, 0)
        thresholds[error_type] = cumulative

    return thresholds
