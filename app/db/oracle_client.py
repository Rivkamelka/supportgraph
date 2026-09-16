"""Oracle client: the legacy PL/SQL loyalty/risk engine.

The agent never recomputes tier or risk score itself -- it calls into
loyalty_pkg exactly as any other internal application would, and reads the
customer_loyalty table that the package maintains. This keeps the business
rule defined in exactly one place (see db/oracle/init/02_loyalty_pkg.sql).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Iterator

from app.config import settings


@contextmanager
def get_connection() -> Iterator[Any]:
    # Imported lazily -- see app/db/mysql_client.py's get_connection() for why.
    import oracledb

    dsn = oracledb.makedsn(settings.oracle_host, settings.oracle_port, service_name=settings.oracle_service)
    conn = oracledb.connect(user=settings.oracle_user, password=settings.oracle_password, dsn=dsn)
    try:
        yield conn
    finally:
        conn.close()


def get_loyalty(customer_id: int) -> dict[str, Any] | None:
    """Reads the pre-computed loyalty row (refreshed by loyalty_pkg at
    container startup, or by refresh_customer_loyalty() below)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT tier, risk_score, last_calculated
            FROM customer_loyalty
            WHERE customer_id = :customer_id
            """,
            customer_id=customer_id,
        )
        row = cur.fetchone()
        if row is None:
            return None
        tier, risk_score, last_calculated = row
        return {"customer_id": customer_id, "tier": tier, "risk_score": float(risk_score), "last_calculated": str(last_calculated)}


def refresh_customer_loyalty(customer_id: int) -> None:
    """Calls loyalty_pkg.refresh_loyalty directly, in case customer_stats
    changed since the last batch refresh (e.g. a new return was logged)."""
    with get_connection() as conn:
        cur = conn.cursor()
        cur.callproc("loyalty_pkg.refresh_loyalty", [customer_id])
        conn.commit()
