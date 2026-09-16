from __future__ import annotations

from app.db import oracle_client
from app.tools.oracle_tool import loyalty_lookup_tool


def test_loyalty_lookup_formats_tier_and_risk(monkeypatch):
    monkeypatch.setattr(
        oracle_client,
        "get_loyalty",
        lambda customer_id: {
            "customer_id": customer_id,
            "tier": "gold",
            "risk_score": 12.5,
            "last_calculated": "2026-01-01",
        },
    )

    result = loyalty_lookup_tool.invoke({"customer_id": 5})

    assert "gold" in result
    assert "12.5" in result


def test_loyalty_lookup_reports_missing_record(monkeypatch):
    monkeypatch.setattr(oracle_client, "get_loyalty", lambda customer_id: None)

    result = loyalty_lookup_tool.invoke({"customer_id": 999})

    assert "No loyalty record found" in result


def test_loyalty_lookup_degrades_gracefully_on_db_error(monkeypatch):
    def boom(customer_id):
        raise RuntimeError("ORA-12154")

    monkeypatch.setattr(oracle_client, "get_loyalty", boom)

    result = loyalty_lookup_tool.invoke({"customer_id": 5})

    assert "Error reaching the loyalty engine" in result
