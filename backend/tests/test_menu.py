from sqlalchemy.orm import Session

from app.models.menu import MenuItem


def test_get_menu_returns_menu_items(client, db_session: Session):
    db_session.add_all(
        [
            MenuItem(
                id=1,
                name="Chips",
                description="Classic potato chips",
                price_cents=199,
                available=True,
            ),
            MenuItem(
                id=2,
                name="Chocolate Bar",
                description="Milk chocolate bar",
                price_cents=249,
                available=True,
            ),
            MenuItem(
                id=3,
                name="Sparkling Water",
                description="Cold sparkling water",
                price_cents=179,
                available=True,
            ),
        ]
    )
    db_session.commit()

    response = client.get("/api/v1/menu")

    assert response.status_code == 200

    menu = response.json()

    assert len(menu) == 3
    assert menu[0] == {
        "id": 1,
        "name": "Chips",
        "description": "Classic potato chips",
        "price_cents": 199,
        "available": True,
    }
