from pydantic import BaseModel


class MenuItemResponse(BaseModel):
    id: int
    name: str
    description: str
    price_cents: int
    available: bool