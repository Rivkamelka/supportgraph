from __future__ import annotations

from app import rate_limit


def setup_function() -> None:
    rate_limit.reset_all()


def test_allows_requests_under_the_limit():
    for _ in range(5):
        limited, _ = rate_limit.is_rate_limited("client-a", max_requests=5, window_seconds=60)
        assert limited is False


def test_blocks_requests_over_the_limit():
    for _ in range(5):
        rate_limit.is_rate_limited("client-a", max_requests=5, window_seconds=60)

    limited, retry_after = rate_limit.is_rate_limited("client-a", max_requests=5, window_seconds=60)

    assert limited is True
    assert retry_after > 0


def test_clients_are_tracked_independently():
    for _ in range(5):
        rate_limit.is_rate_limited("client-a", max_requests=5, window_seconds=60)

    limited, _ = rate_limit.is_rate_limited("client-b", max_requests=5, window_seconds=60)

    assert limited is False


def test_old_hits_fall_out_of_the_window():
    limited, _ = rate_limit.is_rate_limited("client-a", max_requests=1, window_seconds=-1)
    assert limited is False
    # window_seconds=-1 means the first hit is already "expired" by the
    # time we check again, so the client should never be blocked.
    limited, _ = rate_limit.is_rate_limited("client-a", max_requests=1, window_seconds=-1)
    assert limited is False
