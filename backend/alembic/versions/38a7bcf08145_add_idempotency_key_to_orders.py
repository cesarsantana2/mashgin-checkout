"""add idempotency key to orders

Revision ID: 38a7bcf08145
Revises: e3e1ad623517
Create Date: 2026-09-05 15:12:48.343769
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "38a7bcf08145"
down_revision: str | Sequence[str] | None = "e3e1ad623517"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "orders",
        sa.Column(
            "idempotency_key",
            sa.String(length=64),
            nullable=True,
        ),
    )

    orders = sa.table(
        "orders",
        sa.column("id", sa.Integer),
        sa.column("idempotency_key", sa.String),
    )

    connection = op.get_bind()

    existing_orders = connection.execute(
        sa.select(orders.c.id).where(orders.c.idempotency_key.is_(None))
    )

    for row in existing_orders:
        connection.execute(
            orders.update()
            .where(orders.c.id == row.id)
            .values(idempotency_key=f"legacy-order-{row.id}")
        )

    op.alter_column(
        "orders",
        "idempotency_key",
        existing_type=sa.String(length=64),
        nullable=False,
    )

    op.create_unique_constraint(
        "uq_orders_idempotency_key",
        "orders",
        ["idempotency_key"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_orders_idempotency_key",
        "orders",
        type_="unique",
    )

    op.drop_column("orders", "idempotency_key")
