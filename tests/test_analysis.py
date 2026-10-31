import numpy as np
import pytest
from analysis import Scenario, components, total, compare, monte_carlo, sensitivity


def sample():
    return Scenario(100, 50, 10, .5, .2, 1.5)


def test_components_and_total():
    assert components(sample()) == {'Electricity': 50, 'Transport': 10, 'Materials': 15}
    assert total(sample()) == 75


def test_comparison():
    a = sample()
    b = Scenario(50, 50, 10, .5, .2, 1.5)
    assert compare(a, b)['reduction_percent'] == pytest.approx(100/3)


def test_simulation_reproducible():
    x = monte_carlo(sample(), .15, 200, seed=3)
    assert len(x) == 200
    assert np.array_equal(x, monte_carlo(sample(), .15, 200, seed=3))
    assert np.all(x >= 0)


def test_zero_uncertainty():
    assert np.all(monte_carlo(sample(), 0, 10) == 75)


def test_sensitivity():
    assert sensitivity(sample(), .1)['Electricity'] == pytest.approx(5)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        Scenario(-1, 0, 0, 1, 1, 1)
    with pytest.raises(ValueError):
        monte_carlo(sample(), -0.1)
