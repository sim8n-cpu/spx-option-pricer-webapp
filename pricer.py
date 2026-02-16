import math


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def black_scholes_call_put(spot: float, strike: float, t: float, r: float, sigma: float):
    if spot <= 0 or strike <= 0:
        raise ValueError("Spot and strike must be positive")
    if t <= 0:
        raise ValueError("Time to expiry must be positive")
    if sigma <= 0:
        raise ValueError("Volatility must be positive")

    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)

    call = spot * norm_cdf(d1) - strike * math.exp(-r * t) * norm_cdf(d2)
    put = strike * math.exp(-r * t) * norm_cdf(-d2) - spot * norm_cdf(-d1)
    return call, put
