"""Initial migration

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic.
revision = "001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create data_sources table
    op.create_table(
        "data_sources",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("last_updated", sa.DateTime(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_data_sources_id"), "data_sources", ["id"], unique=False)
    op.create_index(op.f("ix_data_sources_name"), "data_sources", ["name"], unique=False)

    # Create regions table
    op.create_table(
        "regions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("parent_region_id", sa.Integer(), nullable=True),
        sa.Column("level", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(
            ["parent_region_id"],
            ["regions.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index(op.f("ix_regions_id"), "regions", ["id"], unique=False)
    op.create_index(op.f("ix_regions_code"), "regions", ["code"], unique=False)

    # Create demographic_data table
    op.create_table(
        "demographic_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("region_id", sa.Integer(), nullable=False),
        sa.Column("data_source_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.Integer(), nullable=True),
        sa.Column("age_min", sa.Integer(), nullable=True),
        sa.Column("age_max", sa.Integer(), nullable=True),
        sa.Column("gender", sa.String(), nullable=False),
        sa.Column("population", sa.Integer(), nullable=False),
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
        op.f("ix_demographic_data_id"), "demographic_data", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_demographic_data_region_id"),
        "demographic_data",
        ["region_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_demographic_data_data_source_id"),
        "demographic_data",
        ["data_source_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_demographic_data_year"), "demographic_data", ["year"], unique=False
    )
    op.create_index(
        "idx_region_year_age_gender",
        "demographic_data",
        ["region_id", "year", "age_min", "gender"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("idx_region_year_age_gender", table_name="demographic_data")
    op.drop_index(op.f("ix_demographic_data_year"), table_name="demographic_data")
    op.drop_index(
        op.f("ix_demographic_data_data_source_id"), table_name="demographic_data"
    )
    op.drop_index(op.f("ix_demographic_data_region_id"), table_name="demographic_data")
    op.drop_index(op.f("ix_demographic_data_id"), table_name="demographic_data")
    op.drop_table("demographic_data")
    op.drop_index(op.f("ix_regions_code"), table_name="regions")
    op.drop_index(op.f("ix_regions_id"), table_name="regions")
    op.drop_table("regions")
    op.drop_index(op.f("ix_data_sources_name"), table_name="data_sources")
    op.drop_index(op.f("ix_data_sources_id"), table_name="data_sources")
    op.drop_table("data_sources")

