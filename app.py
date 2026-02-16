from datetime import date
from dateutil.relativedelta import relativedelta
from flask import Flask, render_template, request
import yfinance as yf

from pricer import black_scholes_call_put

app = Flask(__name__)


DEFAULTS_FALLBACK = {
    "spot": 5000.0,
    "strike": 5000.0,
    "vol_pct": 20.0,
    "risk_free_pct": 4.0,
}


def fetch_market_defaults():
    vals = DEFAULTS_FALLBACK.copy()
    try:
        spx = yf.Ticker("^GSPC").history(period="5d")
        if not spx.empty:
            vals["spot"] = float(spx["Close"].dropna().iloc[-1])
            vals["strike"] = vals["spot"]
    except Exception:
        pass

    try:
        vix = yf.Ticker("^VIX").history(period="5d")
        if not vix.empty:
            vals["vol_pct"] = float(vix["Close"].dropna().iloc[-1])
    except Exception:
        pass

    # 13-week Treasury bill yield index (percent)
    try:
        irx = yf.Ticker("^IRX").history(period="5d")
        if not irx.empty:
            vals["risk_free_pct"] = float(irx["Close"].dropna().iloc[-1])
    except Exception:
        pass

    return vals


def compute_table(spot, strike, t, r, sigma):
    multipliers = [0.90, 0.95, 1.00, 1.05, 1.10]
    rows = []
    for m in multipliers:
        k = strike * m
        call, put = black_scholes_call_put(spot, k, t, r, sigma)
        rows.append({
            "label": f"{int((m - 1.0) * 100):+d}%",
            "strike": k,
            "call": call,
            "put": put,
        })
    return rows


@app.route("/", methods=["GET", "POST"])
def index():
    today = date.today()
    default_expiry = today + relativedelta(months=1)

    defaults = fetch_market_defaults()

    form = {
        "valuation_date": today.isoformat(),
        "expiry_date": default_expiry.isoformat(),
        "spot": defaults["spot"],
        "strike": defaults["strike"],
        "vol_pct": defaults["vol_pct"],
        "risk_free_pct": defaults["risk_free_pct"],
    }

    error = None
    results = None

    if request.method == "POST":
        try:
            form["valuation_date"] = request.form.get("valuation_date", form["valuation_date"])
            form["expiry_date"] = request.form.get("expiry_date", form["expiry_date"])
            form["spot"] = float(request.form.get("spot", form["spot"]))
            form["strike"] = float(request.form.get("strike", form["strike"]))
            form["vol_pct"] = float(request.form.get("vol_pct", form["vol_pct"]))
            form["risk_free_pct"] = float(request.form.get("risk_free_pct", form["risk_free_pct"]))

            vdate = date.fromisoformat(form["valuation_date"])
            edate = date.fromisoformat(form["expiry_date"])
            days = (edate - vdate).days
            if days <= 0:
                raise ValueError("Expiry date must be after valuation date")

            t = days / 365.0
            r = form["risk_free_pct"] / 100.0
            sigma = form["vol_pct"] / 100.0

            call_atm, put_atm = black_scholes_call_put(form["spot"], form["strike"], t, r, sigma)
            table = compute_table(form["spot"], form["strike"], t, r, sigma)

            results = {
                "t_years": t,
                "call_atm": call_atm,
                "put_atm": put_atm,
                "rows": table,
            }
        except Exception as e:
            error = str(e)

    return render_template("index.html", form=form, results=results, error=error)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
