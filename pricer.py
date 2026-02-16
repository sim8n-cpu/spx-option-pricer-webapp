import math


def norm_cdf(x: float) -> float:
    return 0.5 * (1.0 + math.erf(x / math.sqrt(2.0)))


def norm_pdf(x: float) -> float:
    return math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)


def _validate_inputs(spot: float, strike: float, t: float, sigma: float):
    if spot <= 0 or strike <= 0:
        raise ValueError("Spot and strike must be positive")
    if t <= 0:
        raise ValueError("Time to expiry must be positive")
    if sigma <= 0:
        raise ValueError("Volatility must be positive")


def _d1_d2(spot: float, strike: float, t: float, r: float, sigma: float):
    d1 = (math.log(spot / strike) + (r + 0.5 * sigma * sigma) * t) / (sigma * math.sqrt(t))
    d2 = d1 - sigma * math.sqrt(t)
    return d1, d2


def black_scholes_call_put(spot: float, strike: float, t: float, r: float, sigma: float):
    _validate_inputs(spot, strike, t, sigma)
    d1, d2 = _d1_d2(spot, strike, t, r, sigma)

    call = spot * norm_cdf(d1) - strike * math.exp(-r * t) * norm_cdf(d2)
    put = strike * math.exp(-r * t) * norm_cdf(-d2) - spot * norm_cdf(-d1)
    return call, put


def black_scholes_greeks(spot: float, strike: float, t: float, r: float, sigma: float):
    _validate_inputs(spot, strike, t, sigma)
    d1, d2 = _d1_d2(spot, strike, t, r, sigma)

    pdf_d1 = norm_pdf(d1)
    sqrt_t = math.sqrt(t)
    disc = math.exp(-r * t)

    # Shared Greeks
    gamma = pdf_d1 / (spot * sigma * sqrt_t)
    vega = spot * pdf_d1 * sqrt_t  # per +1.00 vol (not 1%)

    # Call Greeks
    call_delta = norm_cdf(d1)
    call_theta = -(spot * pdf_d1 * sigma) / (2 * sqrt_t) - r * strike * disc * norm_cdf(d2)
    call_rho = strike * t * disc * norm_cdf(d2)

    # Put Greeks
    put_delta = call_delta - 1
    put_theta = -(spot * pdf_d1 * sigma) / (2 * sqrt_t) + r * strike * disc * norm_cdf(-d2)
    put_rho = -strike * t * disc * norm_cdf(-d2)

    return {
        "call_delta": call_delta,
        "put_delta": put_delta,
        "gamma": gamma,
        "vega": vega,
        "call_theta": call_theta,
        "put_theta": put_theta,
        "call_rho": call_rho,
        "put_rho": put_rho,
    }
