from fastapi import APIRouter

from app.schemas.menu import MenuItemResponse


router = APIRouter(
    prefix="/menu",
    tags=["menu"],
)


MENU = [
    MenuItemResponse(
        id=1,
        name="Chips",
        description="Classic potato chips",
        price_cents=199,
        available=True,
    ),
    MenuItemResponse(
        id=2,
        name="Chocolate Bar",
        description="Milk chocolate bar",
        price_cents=249,
        available=True,
    ),
    MenuItemResponse(
        id=3,
        name="Sparkling Water",
        description="Cold sparkling water",
        price_cents=179,
        available=True,
    ),
]


@router.get("", response_model=list[MenuItemResponse])
def get_menu():
    return MENU