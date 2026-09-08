from .schemas import CustomerRecordInput, RefundInput

CUSTOMERS = {
    "CUST-12345": {"customer_id": "CUST-12345", "name": "Alice", "status": "active"},
    "CUST-54321": {"customer_id": "CUST-54321", "name": "Bob", "status": "active"},
}

def get_customer_record(customer_id: str):
    data = CustomerRecordInput(customer_id=customer_id)
    return CUSTOMERS.get(data.customer_id,
        {"customer_id": data.customer_id, "status": "not_found"})

def trigger_refund(customer_id: str, amount: float, reason: str):
    data = RefundInput(customer_id=customer_id, amount=amount, reason=reason)
    return {"customer_id": data.customer_id, "amount": data.amount,
            "reason": data.reason, "status": "refund_accepted"}
