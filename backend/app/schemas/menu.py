from pydantic import BaseModel, ConfigDict


class MenuItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str
    price_cents: int
    available: bool
