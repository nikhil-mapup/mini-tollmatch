from datetime import datetime

from typing import Optional

from pydantic import BaseModel


class InvoiceRecord(BaseModel):

    post_date: datetime

    transaction_id: str
    tag_no: Optional[str] = None

    unit: Optional[str] = None

    cost_center: Optional[str] = None

    entry_time: datetime

    exit_time: Optional[datetime] = None

    toll_loc_name_start: Optional[str] = None

    entry_plaza: Optional[str] = None

    toll_loc_name_end: Optional[str] = None

    exit_plaza: Optional[str] = None

    toll_class: Optional[str] = None

    agency: Optional[str] = None

    amount: float

    transactiondesc: Optional[str] = None
