from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime

class DealDiscussed(BaseModel):
    deal_id: Optional[str] = Field(default=None, description="Unique identifier for the deal")
    counterparty_name: str = Field(description="Name of the counterparty in the deal")
    security_name: str = Field(description="Name or identifier of the security being traded")
    maturity_date: Optional[datetime] = Field(default=None, description="Maturity date of the security")
    price: float = Field(description="Price per unit of the security")
    quantity: int = Field(description="Quantity of securities traded")
    transaction_type: Literal["Buy", "Sell"] = Field(description="Type of transaction: Buy or Sell")
    deal_timestamp: datetime = Field(description="Timestamp of when the deal was made")
    brokerage: Optional[float] = Field(default=None, description="Brokerage fee for the transaction")
    face_value: Optional[float] = Field(default=None, description="Face value of the security")
    additional_comments: Optional[str] = Field(default=None, description="Any additional relevant information")

class AnalysisResponse(BaseModel):
    deal_discussed: DealDiscussed
    confidence: float = Field(default=0.7, description="Confidence level of the information extracted")