import pytest

from sbm_store.rating_rule import DEFAULT, white_gain


@pytest.mark.parametrize(
    ("white", "black", "result", "gain"),
    [
        (2500, 2500, "1-0", 50),
        (2500, 2500, "0-1", -50),
        (2500, 2500, "1/2-1/2", 0),
        (2800, 2400, "1-0", 30),
        (2800, 2400, "0-1", -70),
        (2800, 2400, "1/2-1/2", -20),
        (2400, 2800, "1/2-1/2", 20),
        (2400, 2800, "0-1", -30),
        (3600, 2500, "1-0", 1),
        (3600, 2500, "0-1", -100),
        (3600, 2500, "1/2-1/2", -50),
        (2519, 2500, "1-0", 50),
        (2520, 2500, "1-0", 49),
        (2500, 2520, "1-0", 51),
        (2500, 2539, "1/2-1/2", 1),
    ],
)
def test_the_rule_of_e103(white, black, result, gain):
    assert white_gain(white, black, result, DEFAULT) == gain
