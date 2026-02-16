from pricer import black_scholes_call_put, black_scholes_greeks


def test_black_scholes_basic_positive_values():
    c, p = black_scholes_call_put(spot=100, strike=100, t=1.0, r=0.05, sigma=0.2)
    assert c > 0
    assert p > 0


def test_put_call_parity_close():
    s = 120
    k = 110
    t = 0.5
    r = 0.03
    sigma = 0.25
    c, p = black_scholes_call_put(s, k, t, r, sigma)
    lhs = c - p
    rhs = s - k * (2.718281828459045 ** (-r * t))
    assert abs(lhs - rhs) < 1e-6


def test_greeks_sanity():
    g = black_scholes_greeks(spot=100, strike=100, t=1.0, r=0.05, sigma=0.2)
    assert 0 < g["call_delta"] < 1
    assert -1 < g["put_delta"] < 0
    assert g["gamma"] > 0
    assert g["vega"] > 0
