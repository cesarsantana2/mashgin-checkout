from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.menu import MenuItem
from app.models.order import Order


def test_create_order(client, db_session: Session):
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
                id=3,
                name="Sparkling Water",
                description="Cold sparkling water",
                price_cents=179,
                available=True,
            ),
        ]
    )
    db_session.commit()

    response = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "create-order-1"},
        json={
            "items": [
                {"menu_item_id": 1, "quantity": 2},
                {"menu_item_id": 3, "quantity": 1},
            ],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "completed"
    assert data["total_cents"] == 577
    assert len(data["items"]) == 2

    persisted_order = db_session.get(Order, data["id"])

    assert persisted_order is not None
    assert persisted_order.idempotency_key == "create-order-1"
    assert persisted_order.total_cents == 577
    assert len(persisted_order.items) == 2


def test_repeating_idempotency_key_returns_same_order(
    client,
    db_session: Session,
):
    db_session.add(
        MenuItem(
            id=1,
            name="Chips",
            description="Classic potato chips",
            price_cents=199,
            available=True,
        )
    )
    db_session.commit()

    payload = {
        "items": [
            {"menu_item_id": 1, "quantity": 2},
        ],
        "payment": {"method": "card"},
    }

    headers = {"Idempotency-Key": "checkout-abc-123"}

    first_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json=payload,
    )

    second_response = client.post(
        "/api/v1/orders",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201
    assert second_response.status_code == 201

    first_order = first_response.json()
    second_order = second_response.json()

    assert second_order["id"] == first_order["id"]
    assert second_order["total_cents"] == first_order["total_cents"]

    persisted_orders = db_session.scalars(select(Order)).all()

    assert len(persisted_orders) == 1
    assert persisted_orders[0].idempotency_key == "checkout-abc-123"


def test_create_order_without_idempotency_key_returns_422(client):
    response = client.post(
        "/api/v1/orders",
        json={
            "items": [
                {"menu_item_id": 1, "quantity": 1},
            ],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 422


def test_create_order_with_nonexistent_item_returns_400(client):
    response = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "nonexistent-item-1"},
        json={
            "items": [
                {"menu_item_id": 999, "quantity": 1},
            ],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Menu item 999 does not exist"


def test_create_order_with_unavailable_item_returns_409(
    client,
    db_session: Session,
):
    db_session.add(
        MenuItem(
            id=1,
            name="Chips",
            description="Classic potato chips",
            price_cents=199,
            available=False,
        )
    )
    db_session.commit()

    response = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "unavailable-item-1"},
        json={
            "items": [
                {"menu_item_id": 1, "quantity": 1},
            ],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "Menu item 1 is unavailable"


def test_create_order_with_zero_quantity_returns_422(client):
    response = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "zero-quantity-1"},
        json={
            "items": [
                {"menu_item_id": 1, "quantity": 0},
            ],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 422


def test_create_order_with_empty_cart_returns_422(client):
    response = client.post(
        "/api/v1/orders",
        headers={"Idempotency-Key": "empty-cart-1"},
        json={
            "items": [],
            "payment": {"method": "card"},
        },
    )

    assert response.status_code == 422
