"""
Traffic Generator for Demo Checkout Service

Generates realistic traffic patterns and triggers fault scenarios for incident demonstration.
"""

import boto3
import json
import time
import argparse
from datetime import datetime
from typing import Optional

lambda_client = boto3.client("lambda")


def generate_traffic(
    duration_minutes: int = 10,
    requests_per_minute: int = 10,
    function_name: str = "demo-checkout-service",
):
    """
    Generate synthetic traffic to demo app

    Args:
        duration_minutes: How long to generate traffic
        requests_per_minute: Request rate
        function_name: Lambda function to invoke
    """
    print(
        f"🚀 Generating traffic for {duration_minutes} minutes at {requests_per_minute} req/min..."
    )

    end_time = time.time() + (duration_minutes * 60)
    request_count = 0
    errors = 0

    while time.time() < end_time:
        batch_start = time.time()

        for i in range(requests_per_minute):
            order_id = f"ORD-{request_count:06d}"
            user_id = f"USER-{(request_count % 1000) + 1000}"

            try:
                response = lambda_client.invoke(
                    FunctionName=function_name,
                    InvocationType="RequestResponse",  # Synchronous for demo
                    Payload=json.dumps({"order_id": order_id, "user_id": user_id}),
                )

                payload = json.loads(response["Payload"].read())
                status = payload.get("statusCode", 500)

                if status >= 400:
                    errors += 1
                    print(
                        f"❌ [{datetime.now().strftime('%H:%M:%S')}] Order {order_id} failed (status={status})"
                    )
                else:
                    print(
                        f"✅ [{datetime.now().strftime('%H:%M:%S')}] Order {order_id} succeeded"
                    )

            except Exception as e:
                errors += 1
                print(
                    f"⚠️  [{datetime.now().strftime('%H:%M:%S')}] Error invoking Lambda: {e}"
                )

            request_count += 1

        # Calculate sleep time to maintain rate
        elapsed = time.time() - batch_start
        sleep_time = max(0, 60 - elapsed)

        if sleep_time > 0:
            time.sleep(sleep_time)

    error_rate = (errors / request_count * 100) if request_count > 0 else 0
    print(f"\n✅ Traffic generation complete!")
    print(f"   Total requests: {request_count}")
    print(f"   Errors: {errors} ({error_rate:.1f}%)")


def trigger_incident_scenario(
    scenario: str = "db_pool_exhaustion",
    function_name: str = "demo-checkout-service",
    burst_duration_minutes: int = 5,
    burst_rate: int = 30,
):
    """
    Trigger a specific fault scenario and generate burst traffic

    Args:
        scenario: Fault scenario to activate
        function_name: Lambda function name
        burst_duration_minutes: How long to generate burst traffic
        burst_rate: Requests per minute during burst
    """
    print(f"🚨 TRIGGERING INCIDENT SCENARIO: {scenario}")
    print(f"   This will simulate a production incident for demo purposes")
    print()

    # Step 1: Update Lambda environment to activate fault
    print(f"[1/3] Activating fault scenario in Lambda environment...")
    try:
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                "Variables": {
                    "FAULT_SCENARIO": scenario,
                    "FAULT_START_TIME": datetime.now().isoformat(),
                    "LOG_LEVEL": "INFO",
                }
            },
        )
        print(f"   ✅ Environment updated to '{scenario}' scenario")
    except Exception as e:
        print(f"   ❌ Failed to update Lambda configuration: {e}")
        return

    # Step 2: Wait for configuration to propagate
    print(f"\n[2/3] Waiting for configuration to propagate...")
    for i in range(15, 0, -1):
        print(f"   ⏳ {i} seconds remaining...", end="\r")
        time.sleep(1)
    print(f"   ✅ Configuration ready" + " " * 30)

    # Step 3: Generate burst traffic
    print(f"\n[3/3] Generating burst traffic to trigger incident...")
    print(f"   Duration: {burst_duration_minutes} minutes")
    print(f"   Rate: {burst_rate} requests/minute")
    print()

    generate_traffic(
        duration_minutes=burst_duration_minutes,
        requests_per_minute=burst_rate,
        function_name=function_name,
    )

    print(f"\n🎯 INCIDENT SCENARIO COMPLETE!")
    print(f"   Scenario '{scenario}' is now active and generating errors")
    print(f"   Check CloudWatch Logs: /aws/lambda/{function_name}")
    print(f"   Ready to trigger Incident Commander for investigation")


def reset_to_normal(function_name: str = "demo-checkout-service"):
    """Reset Lambda to normal operation"""
    print(f"🔄 Resetting {function_name} to normal operation...")

    try:
        lambda_client.update_function_configuration(
            FunctionName=function_name,
            Environment={
                "Variables": {"FAULT_SCENARIO": "normal", "LOG_LEVEL": "INFO"}
            },
        )
        print(f"✅ Lambda reset to normal operation")
    except Exception as e:
        print(f"❌ Failed to reset: {e}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Traffic generator for demo checkout service"
    )
    parser.add_argument(
        "mode",
        choices=["traffic", "incident", "reset"],
        help="Mode: generate normal traffic, trigger incident, or reset to normal",
    )
    parser.add_argument(
        "--scenario",
        default="db_pool_exhaustion",
        choices=["db_pool_exhaustion", "memory_leak", "cascading_failure"],
        help="Fault scenario to trigger (incident mode only)",
    )
    parser.add_argument("--duration", type=int, default=10, help="Duration in minutes")
    parser.add_argument("--rate", type=int, default=10, help="Requests per minute")
    parser.add_argument(
        "--function", default="demo-checkout-service", help="Lambda function name"
    )

    args = parser.parse_args()

    if args.mode == "traffic":
        generate_traffic(
            duration_minutes=args.duration,
            requests_per_minute=args.rate,
            function_name=args.function,
        )
    elif args.mode == "incident":
        trigger_incident_scenario(
            scenario=args.scenario,
            function_name=args.function,
            burst_duration_minutes=args.duration,
            burst_rate=args.rate,
        )
    elif args.mode == "reset":
        reset_to_normal(function_name=args.function)
