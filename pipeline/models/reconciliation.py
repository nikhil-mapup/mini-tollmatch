from pydantic import BaseModel

class ReconciliationResult(BaseModel):
    trip_id: str
    transaction_id: str
    expected_amount: float
    actual_amount: float
    difference: float
    status: str