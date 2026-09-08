import pandas as pd

from pipeline.common.filters import FilterChain


def test_chain_records_each_rule():
    df = pd.DataFrame({"x": [1, 2, 3, 4]})
    chain = FilterChain()
    out = chain.apply(df, "positive_even", df["x"] % 2 == 0)

    assert len(out) == 2
    assert chain.steps[0].name == "positive_even"
    assert chain.steps[0].dropped == 2
    assert chain.steps[0].survival == 0.5


def test_empty_chain_reports_no_rules():
    assert FilterChain().to_frame().empty


def test_survival_of_an_empty_frame_is_one():
    chain = FilterChain()
    chain.record("noop", 0, 0)
    assert chain.steps[0].survival == 1.0
