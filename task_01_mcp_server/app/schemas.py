from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field, StringConstraints

CustomerId = Annotated[str, StringConstraints(pattern=r"^CUST-\d{5}$")]
RefundAmount = Annotated[float, Field(gt=0)]
RefundReason = Annotated[str, StringConstraints(min_length=10)]

class CustomerRecordInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: CustomerId

class RefundInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    customer_id: CustomerId
    amount: float = Field(gt=0)
    reason: str = Field(min_length=10)
