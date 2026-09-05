from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.menu import MenuItem
from app.schemas.menu import MenuItemResponse

router = APIRouter(
    prefix="/menu",
    tags=["menu"],
)

DbSession = Annotated[Session, Depends(get_db)]


@router.get("", response_model=list[MenuItemResponse])
def get_menu(db: DbSession):
    statement = select(MenuItem).order_by(MenuItem.id)

    return db.scalars(statement).all()
