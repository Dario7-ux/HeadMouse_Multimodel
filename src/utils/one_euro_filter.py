import math
import logging
import numpy as np
import numpy.typing as npt

logger = logging.getLogger("OneEuroFilter")


def _smoothing_factor(t_e: float, cutoff: float) -> float:
    """Calculate the smoothing factor alpha for exponential smoothing.
    
    Args:
        t_e: Time elapsed since last sample (seconds)
        cutoff: Cutoff frequency (Hz)
    
    Returns:
        Smoothing factor alpha in range [0, 1]
    """
    r = 2.0 * math.pi * cutoff * t_e
    return r / (r + 1.0)


def _exponential_smoothing(alpha: float, x: float, x_prev: float) -> float:
    """Apply exponential smoothing (low-pass filter).
    
    Args:
        alpha: Smoothing factor (0 = full smoothing, 1 = no smoothing)
        x: Current raw value
        x_prev: Previous filtered value
    
    Returns:
        Filtered value
    """
    return alpha * x + (1.0 - alpha) * x_prev


class OneEuroFilter:
    """1 Euro Filter for a single dimension.
    
    Attributes:
        min_cutoff: Minimum cutoff frequency (Hz). Lower = more smoothing
                    when still. Decrease to reduce jitter.
        beta: Speed coefficient. Higher = less lag during fast movements.
              Increase to reduce lag.
        d_cutoff: Cutoff frequency for the derivative filter (Hz).
                  Usually left at 1.0.
    """

    def __init__(self, t0: float, x0: float, dx0: float = 0.0,
                 min_cutoff: float = 1.0, beta: float = 0.007,
                 d_cutoff: float = 1.0):
        """Initialize the 1 Euro Filter.
        
        Args:
            t0: Initial timestamp (seconds)
            x0: Initial value
            dx0: Initial derivative estimate
            min_cutoff: Minimum cutoff frequency (Hz). Default 1.0
            beta: Speed coefficient. Default 0.007
            d_cutoff: Derivative cutoff frequency (Hz). Default 1.0
        """
        self.min_cutoff = float(min_cutoff)
        self.beta = float(beta)
        self.d_cutoff = float(d_cutoff)

        self.x_prev = float(x0)
        self.dx_prev = float(dx0)
        self.t_prev = float(t0)

    def __call__(self, t: float, x: float) -> float:
        """Filter a new sample.
        
        Args:
            t: Current timestamp (seconds)
            x: Current raw value
        
        Returns:
            Filtered value
        """
        t_e = t - self.t_prev
        if t_e <= 0:
            return self.x_prev

        # 1. Filter the derivative (speed) of the signal
        a_d = _smoothing_factor(t_e, self.d_cutoff)
        dx = (x - self.x_prev) / t_e
        dx_hat = _exponential_smoothing(a_d, dx, self.dx_prev)

        # 2. Compute adaptive cutoff frequency based on speed
        cutoff = self.min_cutoff + self.beta * abs(dx_hat)

        # 3. Filter the signal with adaptive cutoff
        a = _smoothing_factor(t_e, cutoff)
        x_hat = _exponential_smoothing(a, x, self.x_prev)

        # 4. Store state
        self.x_prev = x_hat
        self.dx_prev = dx_hat
        self.t_prev = t

        return x_hat

    def reset(self, t: float, x: float):
        """Reset filter state with new initial values.
        
        Args:
            t: New initial timestamp
            x: New initial value
        """
        self.x_prev = float(x)
        self.dx_prev = 0.0
        self.t_prev = float(t)


class OneEuroFilter2D:
    """1 Euro Filter for 2D coordinates (x, y).
    
    Convenience wrapper that applies two independent OneEuroFilter instances
    for x and y axes.
    """

    def __init__(self, t0: float, x0: float, y0: float,
                 min_cutoff: float = 1.0, beta: float = 0.007,
                 d_cutoff: float = 1.0):
        """Initialize 2D filter.
        
        Args:
            t0: Initial timestamp (seconds)
            x0: Initial x value
            y0: Initial y value
            min_cutoff: Minimum cutoff frequency (Hz)
            beta: Speed coefficient
            d_cutoff: Derivative cutoff frequency (Hz)
        """
        self.filter_x = OneEuroFilter(t0, x0, min_cutoff=min_cutoff,
                                       beta=beta, d_cutoff=d_cutoff)
        self.filter_y = OneEuroFilter(t0, y0, min_cutoff=min_cutoff,
                                       beta=beta, d_cutoff=d_cutoff)
        logger.info(f"OneEuroFilter2D initialized: min_cutoff={min_cutoff}, "
                    f"beta={beta}, d_cutoff={d_cutoff}")

    def __call__(self, t: float, x: float, y: float) -> tuple[float, float]:
        """Filter a new 2D sample.
        
        Args:
            t: Current timestamp (seconds)
            x: Current raw x value
            y: Current raw y value
        
        Returns:
            Tuple of (filtered_x, filtered_y)
        """
        return self.filter_x(t, x), self.filter_y(t, y)

    def reset(self, t: float, x: float, y: float):
        """Reset both filters with new initial values."""
        self.filter_x.reset(t, x)
        self.filter_y.reset(t, y)

    def update_params(self, min_cutoff: float = None, beta: float = None,
                      d_cutoff: float = None):
        """Update filter parameters dynamically.
        
        Args:
            min_cutoff: New minimum cutoff frequency
            beta: New speed coefficient
            d_cutoff: New derivative cutoff frequency
        """
        changed = False
        if min_cutoff is not None and self.filter_x.min_cutoff != float(min_cutoff):
            self.filter_x.min_cutoff = float(min_cutoff)
            self.filter_y.min_cutoff = float(min_cutoff)
            changed = True
        if beta is not None and self.filter_x.beta != float(beta):
            self.filter_x.beta = float(beta)
            self.filter_y.beta = float(beta)
            changed = True
        if d_cutoff is not None and self.filter_x.d_cutoff != float(d_cutoff):
            self.filter_x.d_cutoff = float(d_cutoff)
            self.filter_y.d_cutoff = float(d_cutoff)
            changed = True

        if changed:
            logger.info(f"OneEuroFilter2D params updated: min_cutoff={min_cutoff}, "
                        f"beta={beta}, d_cutoff={d_cutoff}")
