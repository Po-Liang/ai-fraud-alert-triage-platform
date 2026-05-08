from typing import Optional
from pydantic import BaseModel, Field


class AlertInput(BaseModel):
    customerId: str
    accountId: str
    alertType: str
    amount: float = Field(ge=0)
    currency: str = "JPY"
    country: str
    description: Optional[str] = None
    historicalAverageAmount: float = Field(default=0, ge=0)
    isNewBeneficiary: bool = False
    transactionCountLastHour: int = Field(default=0, ge=0)
