from pydantic import BaseModel

class ExpectedToll(BaseModel):
    trip_id: str
    amount: float
    distance: float
    polyline: str
    tolls: list