"""Add industrial data table

Revision ID: 002_industrial
Revises: 001_initial
Create Date: 2024-12-19 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "002_industrial"
down_revision = "001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create industrial_data table
    op.create_table(
        "industrial_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("nace_code", sa.String(), nullable=True),
        sa.Column("index_value", sa.Integer(), nullable=True),
        sa.Column("unit", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["data_source_id"],
            ["data_sources.id"],
        ),
        sa.ForeignKeyConstraint(
            ["region_id"],
            ["regions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_industrial_data_id"), "industrial_data", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_industrial_data_region_id"),
        "industrial_data",
        ["region_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_industrial_data_data_source_id"),
        "industrial_data",
        ["data_source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_industrial_data_year"), "industrial_data", ["year"], unique=False
    )
    op.create_index(
        "idx_industrial_region_year_month",
        "industrial_data",
        ["region_id", "year", "month", "nace_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_industrial_region_year_month", table_name="industrial_data")
    op.drop_index(op.f("ix_industrial_data_year"), table_name="industrial_data")
    op.drop_index(
        op.f("ix_industrial_data_data_source_id"), table_name="industrial_data"
    )
    op.drop_index(op.f("ix_industrial_data_region_id"), table_name="industrial_data")
    op.drop_index(op.f("ix_industrial_data_id"), table_name="industrial_data")
    op.drop_table("industrial_data")
