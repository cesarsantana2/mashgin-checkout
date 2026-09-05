from typing import Literal

from pydantic import BaseModel, Field


class OrderItemCreate(BaseModel):
    menu_item_id: int
    quantity: int = Field(gt=0)


class PaymentCreate(BaseModel):
    method: Literal["card"] = "card"


class OrderCreate(BaseModel):
    items: list[OrderItemCreate] = Field(min_length=1)
    payment: PaymentCreate


class OrderItemResponse(BaseModel):
    menu_item_id: int
    item_name: str
    quantity: int
    unit_price_cents: int


class OrderResponse(BaseModel):
    id: int
    status: str
    total_cents: int
    items: list[OrderItemResponse]
