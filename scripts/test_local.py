"""
Local testing script for demo checkout service

This script simulates Lambda invocations with different fault scenarios
and shows the structured JSON logs.
"""

import json
import os
import sys
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from lambda_handler import handler


class MockLambdaContext:
    """Mock AWS Lambda context for local testing"""

    def __init__(self):
        self.request_id = f"local-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        self.function_version = "$LATEST"
        self.function_name = "demo-checkout-service"
        self.memory_limit_in_mb = 512
        self.invoked_function_arn = (
            "arn:aws:lambda:us-east-1:123456789012:function:demo-checkout-service"
        )
        self.aws_request_id = self.request_id
        self.log_group_name = "/aws/lambda/demo-checkout-service"
        self.log_stream_name = f"2026/02/06/[$LATEST]{self.request_id}"


def test_scenario(scenario_name: str, num_requests: int = 5):
    """
    Test a specific fault scenario

    Args:
        scenario_name: One of 'normal', 'db_pool_exhaustion', 'memory_leak', 'cascading_failure'
        num_requests: Number of requests to simulate
    """
    print("\n" + "=" * 80)
    print(f"🧪 Testing Scenario: {scenario_name.upper()}")
    print("=" * 80)

    # Set fault scenario in environment
    os.environ["FAULT_SCENARIO"] = scenario_name

    results = {"success": 0, "timeout": 0, "error": 0}

    for i in range(num_requests):
        print(f"Request {i + 1}/{num_requests}")
        print("-" * 40)

        # Create test event
        event = {
            "order_id": f"ORD-{scenario_name.upper()}-{i + 1:03d}",
            "user_id": f"USER-{1000 + i}",
        }

        # Create mock context
        context = MockLambdaContext()

        # Invoke handler
        try:
            result = handler(event, context)
            response_body = json.loads(result["body"])

            if result["statusCode"] == 200:
                results["success"] += 1
                print(f"✅ SUCCESS: {response_body['message']}")
            elif result["statusCode"] == 504:
                results["timeout"] += 1
                print(f"⏱️  TIMEOUT: {response_body['message']}")
            else:
                results["error"] += 1
                print(f"❌ ERROR: {response_body['message']}")

        except Exception as e:
            results["error"] += 1
            print(f"💥 EXCEPTION: {str(e)}")

    # Print summary
    print("\n" + "=" * 80)
    print("📊 RESULTS SUMMARY")
    print("=" * 80)
    print(
        f"✅ Successful: {results['success']}/{num_requests} ({results['success'] / num_requests * 100:.0f}%)"
    )
    print(
        f"⏱️  Timeouts:   {results['timeout']}/{num_requests} ({results['timeout'] / num_requests * 100:.0f}%)"
    )
    print(
        f"❌ Errors:     {results['error']}/{num_requests} ({results['error'] / num_requests * 100:.0f}%)"
    )
    print("=" * 80)

    return results


def main():
    """Run local tests"""
    print("\n🚀 Demo Checkout Service - Local Testing")
    print("=" * 80)
    print("\nThis script tests different fault injection scenarios locally.")
    print("Check the logs above for structured JSON output from Lambda Powertools.\n")

    # Test different scenarios
    scenarios = [
        ("normal", 10),
        ("db_pool_exhaustion", 10),
    ]

    all_results = {}

    for scenario, num_requests in scenarios:
        results = test_scenario(scenario, num_requests)
        all_results[scenario] = results

    # Final summary
    print("\n\n" + "=" * 80)
    print("🎯 OVERALL SUMMARY")
    print("=" * 80)

    for scenario, results in all_results.items():
        total = sum(results.values())
        print(f"\n{scenario.upper()}:")
        print(f"  Success Rate: {results['success'] / total * 100:.0f}%")
        print(f"  Timeout Rate: {results['timeout'] / total * 100:.0f}%")
        print(f"  Error Rate:   {results['error'] / total * 100:.0f}%")

    print("\n" + "=" * 80)
    print("\n💡 TIP: Logs are printed to stdout in JSON format.")
    print("   In AWS CloudWatch, these would be searchable via Logs Insights.")
    print("\n✅ Testing complete!")


if __name__ == "__main__":
    main()
