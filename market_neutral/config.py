"""Explicit, untuned research assumptions."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ResearchConfig:
    seed: int = 42
    observations: int = 756
    assets: int = 36
    sectors: int = 6
    correlation_window: int = 126
    beta_window: int = 126
    volatility_window: int = 63
    signal_window: int = 5
    neighbours: int = 5
    minimum_correlation: float = 0.20
    diffusion_time: float = 1.0
    gross_limit: float = 1.0
    position_limit: float = 0.08
    trading_cost_bps: float = 5.0
    annual_borrow_rate: float = 0.02
    initial_capital: float = 100_000.0
    annualisation: int = 252

    def __post_init__(self):
        integer_fields = ("seed", "observations", "assets", "sectors",
                          "correlation_window", "beta_window", "volatility_window",
                          "signal_window", "neighbours", "annualisation")
        for name in integer_fields:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int):
                raise ValueError(f"{name} must be an integer")
        if self.seed < 0 or self.assets < 4 or not 1 <= self.sectors <= self.assets:
            raise ValueError("Invalid simulation dimensions or seed")
        if min(self.correlation_window, self.beta_window, self.volatility_window) < 3:
            raise ValueError("Estimation windows must contain at least three returns")
        if self.signal_window < 1 or self.annualisation < 1:
            raise ValueError("Signal window and annualisation must be positive")
        if self.observations <= self.warmup + 3:
            raise ValueError("Need enough observations after warm-up")
        if not 1 <= self.neighbours < self.assets:
            raise ValueError("neighbours must be between 1 and assets - 1")
        for name, value in self.__dict__.items():
            if isinstance(value, (int, float)) and not math.isfinite(value):
                raise ValueError(f"{name} must be finite")
        if not 0 <= self.minimum_correlation < 1 or self.diffusion_time < 0:
            raise ValueError("Invalid graph settings")
        if not 0 < self.gross_limit <= 2 or not 0 < self.position_limit <= 1:
            raise ValueError("Invalid exposure limits")
        if not 0 <= self.trading_cost_bps <= 100 or self.annual_borrow_rate < 0:
            raise ValueError("Invalid cost settings")
        if self.initial_capital <= 0:
            raise ValueError("initial_capital must be positive")

    @property
    def warmup(self):
        return max(self.correlation_window, self.beta_window,
                   self.volatility_window, self.signal_window)
