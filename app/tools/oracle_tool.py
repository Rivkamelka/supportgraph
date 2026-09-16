"""LangChain Tool wrapper around the Oracle client -- loyalty/risk engine."""

from __future__ import annotations

from langchain_core.tools import tool

from app.db import oracle_client


@tool
def loyalty_lookup_tool(customer_id: int) -> str:
    """Look up a customer's loyalty tier and risk score, computed by the
    Oracle PL/SQL loyalty_pkg package, given their numeric customer id."""
    try:
        loyalty = oracle_client.get_loyalty(customer_id)
    except Exception as exc:  # pragma: no cover - depends on live DB
        return f"Error reaching the loyalty engine: {exc}"

    if loyalty is None:
        return f"No loyalty record found for customer {customer_id}."

    return (
        f"Customer {customer_id} is '{loyalty['tier']}' tier with a risk score of "
        f"{loyalty['risk_score']:.1f}/100 (last calculated {loyalty['last_calculated']})."
    )
