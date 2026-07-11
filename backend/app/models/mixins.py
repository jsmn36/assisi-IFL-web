"""SQLAlchemy mixins used by tenant-scoped models.

Any domain table that stores tenant-owned data must inherit
:class:`TenantScopedMixin`. The SQLAlchemy session filter registered in
:mod:`app.database` uses this as the discriminator — tables that do NOT
inherit this mixin are considered tenant-neutral (e.g. the ``tenants``
table itself, ``refresh_tokens``, rate-limit configuration).
"""
from __future__ import annotations

from sqlalchemy import Column, ForeignKey, Integer
from sqlalchemy.orm import declared_attr


class TenantScopedMixin:
    """Mixin that adds an indexed, NOT NULL ``tenant_id`` to a model.

    During the online-migration window the column is initially added as
    nullable; the NOT NULL constraint is set after backfill completes (see
    the Alembic migration). Code should treat it as always populated.
    """

    @declared_attr
    def tenant_id(cls):  # noqa: N805 — SQLAlchemy convention
        return Column(
            Integer,
            ForeignKey("tenants.id", ondelete="RESTRICT"),
            nullable=False,
            index=True,
        )
