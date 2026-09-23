import os
from dotenv import load_dotenv
import instructor
from litellm import completion
from schema import PurchaseOrder

load_dotenv()

# Wrap LiteLLM with Instructor's patching engine
# MODE_JSON or MODE_TOOLS forces standard tool/function-calling protocols
client = instructor.from_litellm(completion)


def extract_purchase_order(raw_text: str) -> PurchaseOrder:
    """
    Extracts structured PurchaseOrder data from unstructured text.
    If the LLM fails Pydantic validation, Instructor captures the ValidationError,
    appends it to the message history, and retries up to max_retries times.
    """
    response: PurchaseOrder = client.chat.completions.create(
        
        model="groq/openai/gpt-oss-120b",
        response_model=PurchaseOrder,
        max_retries=3,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are an enterprise extraction pipeline. "
                    "Extract purchase order details from the provided text. "
                    "Calculate item totals if they are missing or implied."
                ),
            },
            {
                "role": "user",
                "content": raw_text,
            },
        ],
    )
    return response


if __name__ == "__main__":
    messy_input = """
    Hey Anthony, sent over the 50 bags of layer feed from Akosua Farms yesterday (Sept 21 2026). 
    Each bag is 120 GHS. Also threw in 2 industrial heat lamps for 250 GHS each. 
    Total hasn't been settled yet, let me know when you receive them at the depot.
    """

    print("--- Ingesting Raw Input ---")
    po = extract_purchase_order(messy_input)

    print("\n--- Extraction Succeeded (Pydantic Model Instance) ---")
    print(f"Vendor:      {po.vendor_name}")
    print(f"Currency:    {po.currency}")
    print(f"Status:      {po.payment_status.value}")
    print(f"Date:        {po.order_date}")
    print(f"Grand Total: {po.grand_total} {po.currency}")
    print("\nLine Items:")
    for item in po.items:
        print(f" - {item.description}: {item.quantity} units @ {item.unit_price} = {item.total_price}")

    print("\n--- Validated JSON Dump for Downstream APIs ---")
    print(po.model_dump_json(indent=2))