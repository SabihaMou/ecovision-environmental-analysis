"""Transparent, simplified environmental-impact calculations (not a full LCA)."""
from dataclasses import dataclass
import numpy as np

@dataclass(frozen=True)
class Scenario:
    electricity_kwh: float
    transport_km: float
    material_kg: float
    electricity_factor: float
    transport_factor: float
    material_factor: float

    def __post_init__(self):
        if any(v < 0 for v in vars(self).values()):
            raise ValueError('Inputs and emission factors must be non-negative')


def components(s: Scenario) -> dict[str, float]:
    return {
        'Electricity': s.electricity_kwh * s.electricity_factor,
        'Transport': s.transport_km * s.transport_factor,
        'Materials': s.material_kg * s.material_factor,
    }


def total(s: Scenario) -> float:
    return sum(components(s).values())


def compare(base: Scenario, alternative: Scenario) -> dict[str, float]:
    a, b = total(base), total(alternative)
    return {'baseline': a, 'alternative': b, 'difference': b-a, 'reduction_percent': (a-b)/a*100 if a else 0.0}


def monte_carlo(s: Scenario, relative_uncertainty: float = .15, samples: int = 5000, seed: int = 42) -> np.ndarray:
    """Assume independent lognormal emission factors, specified relative SD; quantities fixed."""
    if not 0 <= relative_uncertainty <= 1:
        raise ValueError('Relative uncertainty must be between 0 and 1')
    if samples < 1:
        raise ValueError('Samples must be positive')
    rng = np.random.default_rng(seed)
    quantities = np.array([s.electricity_kwh, s.transport_km, s.material_kg], dtype=float)
    factors = np.array([s.electricity_factor, s.transport_factor, s.material_factor], dtype=float)
    if relative_uncertainty == 0:
        return np.full(samples, total(s))
    sigma = np.sqrt(np.log1p(relative_uncertainty**2))
    multiplier = rng.lognormal(mean=-sigma**2/2, sigma=sigma, size=(samples, 3))
    return (multiplier * factors * quantities).sum(axis=1)


def sensitivity(s: Scenario, change: float = .10) -> dict[str, float]:
    """Change each activity quantity by +change, keeping other inputs fixed."""
    if change < 0:
        raise ValueError('Change must be non-negative')
    return {key: value * change for key, value in components(s).items()}
