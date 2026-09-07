"""Baseline schema — frozen snapshot as of this migration's authoring date

This is the first migration. It executes a FROZEN SNAPSHOT of the canonical
schema — alembic/versions/0001_baseline_snapshot.sql — not a live read of
Database/shema.sql.

*** THIS FILE MUST NEVER READ Database/shema.sql AT RUNTIME AGAIN. ***

Why: an earlier version of this migration did read Database/shema.sql live,
on the theory that "canonical schema lives in one file, so the baseline
migration should just execute that file." That's wrong for a migration
specifically: Database/shema.sql is a living document that gets edited
directly for every new schema change (correct, intended workflow), which
means a migration that reads it live silently absorbs every later edit too
— so it stops representing "the schema as of this revision" and instead
represents "the schema as of whenever this migration happens to run." That
caused a real DuplicateColumn failure: migration 0002 tried to
ALTER TABLE test_runs ADD COLUMN executed_by, but by the time both
migrations ran together, this migration's live read of Database/shema.sql
already included that column (because it had already been added to the
canonical file for 0002), so 0002's ADD COLUMN collided with a column 0001
had just created.

The fix: 0001_baseline_snapshot.sql is a point-in-time copy, committed
alongside this file, that never changes again once history depends on it.
Every schema change after this one must be its own new migration with real
CREATE TABLE / ALTER TABLE statements for just that delta — never another
full-schema dump, and never a live read of Database/shema.sql.

(For the record: this snapshot already includes test_runs.executed_by. The
migration that was originally going to add that column separately — 0002 —
was deleted rather than kept, because it had never successfully applied to
any real database; confirmed via a clean `psql -c "\\dt"` / missing
alembic_version table on the only environment this had ever been run
against before this fix.)

Revision ID: 0001
Revises:
Create Date: 2026-09-06

"""
import os
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Frozen snapshot living next to this migration file — NOT Database/shema.sql.
_SNAPSHOT_SQL_PATH = os.path.join(os.path.dirname(__file__), "0001_baseline_snapshot.sql")


def upgrade() -> None:
    with open(_SNAPSHOT_SQL_PATH, "r", encoding="utf-8") as f:
        sql_content = f.read()
    # Passed as one string, not split on ';' in Python — Postgres's own
    # parser (simple query protocol) handles multiple statements per call
    # and correctly ignores semicolons inside comments/string literals.
    op.execute(sql_content)


def downgrade() -> None:
    # Baseline downgrade: drop everything this migration created. Simpler and
    # safer than enumerating ~25 tables in reverse FK order.
    op.execute("DROP SCHEMA public CASCADE")
    op.execute("CREATE SCHEMA public")
