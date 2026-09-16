from app.agent.router import _heuristic_routes


def test_routes_order_question_to_sql():
    assert "sql" in _heuristic_routes("What's the status of order 1042?")


def test_routes_product_question_to_mongo():
    assert "mongo" in _heuristic_routes("Do you have a wireless keyboard in stock?")


def test_routes_loyalty_question_to_oracle():
    assert "oracle" in _heuristic_routes("What loyalty tier is customer 5 in?")


def test_routes_policy_question_to_rag():
    assert "rag" in _heuristic_routes("What is your return policy for defective items?")


def test_unmatched_question_falls_back_to_rag():
    routes = _heuristic_routes("hello, are you a real person?")
    assert routes == ["rag"]


def test_can_combine_multiple_routes():
    routes = _heuristic_routes("Is order 12 from a platinum tier customer?")
    assert "sql" in routes
    assert "oracle" in routes
