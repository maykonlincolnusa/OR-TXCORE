from app.fraud.synthetic import as_rows

def test_synthetic_stream_is_deterministic_and_has_only_safe_money_types():
    first, second = as_rows(7, 20), as_rows(7, 20)
    assert first == second
    assert isinstance(first[0]["amount_minor"], int)
    assert {row["label"] for row in first} <= {"FRAUD", "LEGITIMATE"}
