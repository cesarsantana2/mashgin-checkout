from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.menu import MenuItem

MENU_ITEMS = [
    {
        "id": 1,
        "name": "Chips",
        "description": "Classic potato chips",
        "price_cents": 199,
        "available": True,
    },
    {
        "id": 2,
        "name": "Chocolate Bar",
        "description": "Milk chocolate bar",
        "price_cents": 249,
        "available": True,
    },
    {
        "id": 3,
        "name": "Sparkling Water",
        "description": "Cold sparkling water",
        "price_cents": 179,
        "available": True,
    },
]


def seed_menu() -> None:
    with SessionLocal() as db:
        existing_ids = set(db.scalars(select(MenuItem.id)).all())

        items_to_create = [
            MenuItem(**item) for item in MENU_ITEMS if item["id"] not in existing_ids
        ]

        if not items_to_create:
            print("Menu already seeded.")
            return

        db.add_all(items_to_create)
        db.commit()

        print(f"Seeded {len(items_to_create)} menu items.")


if __name__ == "__main__":
    seed_menu()
