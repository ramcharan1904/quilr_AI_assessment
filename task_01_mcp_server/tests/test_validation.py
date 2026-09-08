import pytest
from pydantic import ValidationError
from app.schemas import CustomerRecordInput, RefundInput

def test_customer_id():
    CustomerRecordInput(customer_id="CUST-12345")
    with pytest.raises(ValidationError):
        CustomerRecordInput(customer_id="bad")

def test_refund():
    RefundInput(customer_id="CUST-12345", amount=1.0,
                reason="Customer requested refund")
    with pytest.raises(ValidationError):
        RefundInput(customer_id="CUST-12345", amount=0,
                    reason="Customer requested refund")
