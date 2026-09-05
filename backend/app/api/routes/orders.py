from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.menu import MenuItem
from app.models.order import Order, OrderItem
from app.schemas.order import OrderCreate, OrderResponse

router = APIRouter(
    prefix="/orders",
    tags=["orders"],
)

DbSession = Annotated[Session, Depends(get_db)]
IdempotencyKey = Annotated[
    str,
    Header(alias="Idempotency-Key", min_length=1, max_length=64),
]


@router.post(
    "",
    response_model=OrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_order(
    order_data: OrderCreate,
    db: DbSession,
    idempotency_key: IdempotencyKey,
):
    existing_order = db.scalar(
        select(Order).where(Order.idempotency_key == idempotency_key)
    )

    if existing_order is not None:
        return existing_order

    menu_item_ids = [item.menu_item_id for item in order_data.items]

    statement = select(MenuItem).where(MenuItem.id.in_(menu_item_ids))
    menu_items = db.scalars(statement).all()

    menu_by_id = {item.id: item for item in menu_items}

    order_items = []
    total_cents = 0

    for requested_item in order_data.items:
        menu_item = menu_by_id.get(requested_item.menu_item_id)

        if menu_item is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Menu item {requested_item.menu_item_id} does not exist",
            )

        if not menu_item.available:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Menu item {menu_item.id} is unavailable",
            )

        total_cents += menu_item.price_cents * requested_item.quantity

        order_items.append(
            OrderItem(
                menu_item_id=menu_item.id,
                item_name=menu_item.name,
                quantity=requested_item.quantity,
                unit_price_cents=menu_item.price_cents,
            )
        )

    order = Order(
        idempotency_key=idempotency_key,
        status="completed",
        total_cents=total_cents,
        items=order_items,
    )

    db.add(order)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

        existing_order = db.scalar(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )

        if existing_order is not None:
            return existing_order

        raise

    db.refresh(order)

    return order
