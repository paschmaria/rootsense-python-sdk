"""Basic RootSense SDK usage example.

This example demonstrates:
- SDK initialization
- Exception capturing
- Adding context (user, tags, breadcrumbs)
- Custom fingerprinting
- Message capturing
"""

import rootsense
import time


def main():
    # Initialize RootSense
    print("Initializing RootSense...")
    rootsense.init(
        api_key="your-api-key",  # Replace with your actual API key
        project_id="your-project-id",  # Replace with your project ID
        environment="production",
        debug=True,  # Enable debug logging
        send_default_pii=False,
    )

    # Set user context
    print("\n1. Setting user context...")
    rootsense.set_user(
        id="user-123",
        email="john.doe@example.com",
        username="johndoe",
        ip_address="192.168.1.1"
    )

    # Add custom tags
    print("2. Adding custom tags...")
    rootsense.set_tag("environment", "production")
    rootsense.set_tag("version", "1.0.0")
    rootsense.set_tag("feature_flag", "new_checkout")

    # Add custom context
    print("3. Setting custom context...")
    rootsense.set_context("payment", {
        "method": "credit_card",
        "amount": 99.99,
        "currency": "USD"
    })

    # Add breadcrumbs for debugging trail
    print("4. Adding breadcrumbs...")
    rootsense.push_breadcrumb(
        message="User navigated to checkout",
        category="navigation",
        level="info"
    )
    
    rootsense.push_breadcrumb(
        message="Payment form submitted",
        category="ui.interaction",
        level="info",
        data={"form_id": "payment-form"}
    )

    # Capture a simple message
    print("\n5. Capturing info message...")
    rootsense.capture_message(
        "Payment processing started",
        level="info",
        extra={"transaction_id": "txn-12345"}
    )

    # Simulate an error and capture it
    print("6. Simulating and capturing an exception...")
    try:
        # Simulate a payment processing error
        process_payment(amount=-100)
    except Exception as e:
        event_id = rootsense.capture_exception(e)
        print(f"   Exception captured! Event ID: {event_id}")

    # Capture exception with custom fingerprint
    print("\n7. Capturing exception with custom fingerprint...")
    try:
        raise ValueError("Database connection timeout")
    except Exception as e:
        event_id = rootsense.capture_exception(
            e,
            fingerprint=["database", "timeout", "payment-service"]
        )
        print(f"   Exception captured with custom fingerprint! Event ID: {event_id}")

    # Add more breadcrumbs before another error
    print("\n8. Adding more breadcrumbs and capturing another error...")
    rootsense.push_breadcrumb(
        message="Retrying payment processing",
        category="process",
        level="warning"
    )
    
    try:
        validate_card_number("1234-5678-9012-3456")
    except Exception as e:
        event_id = rootsense.capture_exception(
            e,
            extra={
                "retry_count": 3,
                "timeout_seconds": 30
            }
        )
        print(f"   Validation error captured! Event ID: {event_id}")

    # Capture a warning message
    print("\n9. Capturing warning message...")
    rootsense.capture_message(
        "Payment processing taking longer than expected",
        level="warning",
        extra={"elapsed_time": 5.2}
    )

    # Demonstrate error in a nested function
    print("\n10. Capturing error from nested function...")
    try:
        nested_function_call()
    except Exception as e:
        event_id = rootsense.capture_exception(e)
        print(f"    Nested error captured! Event ID: {event_id}")

    print("\n11. Flushing and closing client...")
    # Ensure all events are sent before exiting
    client = rootsense.get_client()
    if client:
        client.close()
    
    print("\nDone! Check your RootSense dashboard to see the captured events.")


def process_payment(amount: float) -> dict:
    """Simulate payment processing."""
    if amount <= 0:
        raise ValueError(f"Invalid payment amount: {amount}. Must be positive.")
    
    # Simulate processing
    time.sleep(0.1)
    return {"status": "success", "transaction_id": "txn-12345"}


def validate_card_number(card: str) -> bool:
    """Validate credit card number."""
    if not card or len(card.replace("-", "")) < 16:
        raise ValueError("Invalid card number: must be at least 16 digits")
    return True


def nested_function_call():
    """Demonstrate error in nested function."""
    def level1():
        def level2():
            def level3():
                raise RuntimeError("Error in deeply nested function")
            level3()
        level2()
    level1()


if __name__ == "__main__":
    main()
