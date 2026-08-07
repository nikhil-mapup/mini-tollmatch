from datetime import datetime

from typing import Optional

from pydantic import BaseModel


class InvoiceRecord(BaseModel):

    post_date: datetime

    transaction_id: str

    tag_no: str

    unit: Optional[str] = None

    cost_center: Optional[str] = None

    entry_time: datetime

    exit_time: Optional[datetime] = None

    toll_loc_name_start: Optional[str]

    entry_plaza: Optional[str]

    toll_loc_name_end: Optional[str]

    exit_plaza: Optional[str]

    toll_class: Optional[str]

    agency: Optional[str]

    amount: float

    transactiondesc: Optional[str]
