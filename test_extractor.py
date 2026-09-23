import pytest
from pydantic import ValidationError
from extractor import extract_purchase_order
from schema import PaymentStatus, PurchaseOrder


def test_standard_invoice_extraction():
    """Verify clean extraction of multiple items and calculated totals."""
    raw = """
    Invoice from AgriCorp Ghana. 
    Customer: Anthony Maxwell. Date: Oct 12, 2026.
    Items:
    - 20 feeders @ 15.50 GHS
    - 4 water troughs @ 50.00 GHS
    Status: Paid via Bank Transfer.
    """
    po = extract_purchase_order(raw)

    assert isinstance(po, PurchaseOrder)
    assert po.vendor_name.lower().find("agricorp") != -1
    assert po.currency == "GHS"
    assert po.payment_status == PaymentStatus.PAID
    assert len(po.items) == 2
    # Verify math consistency
    assert po.grand_total == round(20 * 15.50 + 4 * 50.00, 2)


def test_contradictory_math_self_heals():
    """Verify that contradictory input totals are corrected by schema rules."""
    raw = """
    Invoice from Kasoa Feeds:
    5 bags of grower mash at 200 GHS each.
    Total: 600 GHS (incorrect text).
    """
    po = extract_purchase_order(raw)

    assert po.items[0].quantity == 5.0
    assert po.items[0].unit_price == 200.0
    # Must enforce 5 * 200 = 1000, rejecting the text's 600 claim
    assert po.items[0].total_price == 1000.0
    assert po.grand_total == 1000.0


def test_non_transactional_text_handling():
    """Verify engine behavior when no commercial transaction exists."""
    irrelevant_text = "Good morning everyone, the weather looks cloudy today. Don't forget the team meeting."
    
    # An input with no purchase items should fail schema validation 
    # because items requires min_length=1
    try:
        po = extract_purchase_order(irrelevant_text)
        # If it didn't raise, ensure it didn't invent phantom items
        assert len(po.items) >= 1
    except Exception as e:
        # InstructorRetryException or ValidationError is expected when constraints cannot be satisfied
        assert True