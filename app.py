import csv
import io
import os
from datetime import date

from dateutil.relativedelta import relativedelta
from flask import Flask, Response, render_template, request
import yfinance as yf

from pricer import black_scholes_call_put, black_scholes_greeks

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


def default_form():
    today = date.today()
    default_expiry = today + relativedelta(months=1)
    defaults = fetch_market_defaults()
    return {
        "valuation_date": today.isoformat(),
        "expiry_date": default_expiry.isoformat(),
        "spot": defaults["spot"],
        "strike": defaults["strike"],
        "vol_pct": defaults["vol_pct"],
        "risk_free_pct": defaults["risk_free_pct"],
    }


def parse_form(source, base_form):
    form = base_form.copy()
    form["valuation_date"] = source.get("valuation_date", form["valuation_date"])
    form["expiry_date"] = source.get("expiry_date", form["expiry_date"])
    form["spot"] = float(source.get("spot", form["spot"]))
    form["strike"] = float(source.get("strike", form["strike"]))
    form["vol_pct"] = float(source.get("vol_pct", form["vol_pct"]))
    form["risk_free_pct"] = float(source.get("risk_free_pct", form["risk_free_pct"]))
    return form


def compute_table(spot, strike, t, r, sigma):
    multipliers = [0.90, 0.95, 1.00, 1.05, 1.10]
    rows = []
    for m in multipliers:
        k = strike * m
        call, put = black_scholes_call_put(spot, k, t, r, sigma)
        g = black_scholes_greeks(spot, k, t, r, sigma)
        rows.append({
            "label": f"{int((m - 1.0) * 100):+d}%",
            "strike": k,
            "call": call,
            "put": put,
            **g,
        })
    return rows


def calculate_results(form):
    vdate = date.fromisoformat(form["valuation_date"])
    edate = date.fromisoformat(form["expiry_date"])
    days = (edate - vdate).days
    if days <= 0:
        raise ValueError("Expiry date must be after valuation date")

    t = days / 365.0
    r = form["risk_free_pct"] / 100.0
    sigma = form["vol_pct"] / 100.0

    call_atm, put_atm = black_scholes_call_put(form["spot"], form["strike"], t, r, sigma)
    atm_greeks = black_scholes_greeks(form["spot"], form["strike"], t, r, sigma)
    table = compute_table(form["spot"], form["strike"], t, r, sigma)

    return {
        "t_years": t,
        "call_atm": call_atm,
        "put_atm": put_atm,
        "atm_greeks": atm_greeks,
        "rows": table,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    form = default_form()
    error = None
    results = None

    if request.method == "POST":
        try:
            form = parse_form(request.form, form)
            results = calculate_results(form)
        except Exception as e:
            error = str(e)

    return render_template("index.html", form=form, results=results, error=error)


@app.route("/export_csv", methods=["GET"])
def export_csv():
    form = parse_form(request.args, default_form())
    results = calculate_results(form)

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow(["valuation_date", form["valuation_date"]])
    writer.writerow(["expiry_date", form["expiry_date"]])
    writer.writerow(["spot", f"{form['spot']:.6f}"])
    writer.writerow(["base_strike", f"{form['strike']:.6f}"])
    writer.writerow(["volatility_pct", f"{form['vol_pct']:.6f}"])
    writer.writerow(["risk_free_pct", f"{form['risk_free_pct']:.6f}"])
    writer.writerow([])

    writer.writerow(["ATM prices"])
    writer.writerow(["call", f"{results['call_atm']:.10f}"])
    writer.writerow(["put", f"{results['put_atm']:.10f}"])
    writer.writerow([])

    g = results["atm_greeks"]
    writer.writerow(["ATM greeks"])
    writer.writerow(["call_delta", f"{g['call_delta']:.10f}"])
    writer.writerow(["put_delta", f"{g['put_delta']:.10f}"])
    writer.writerow(["gamma", f"{g['gamma']:.10f}"])
    writer.writerow(["vega", f"{g['vega']:.10f}"])
    writer.writerow(["call_theta", f"{g['call_theta']:.10f}"])
    writer.writerow(["put_theta", f"{g['put_theta']:.10f}"])
    writer.writerow(["call_rho", f"{g['call_rho']:.10f}"])
    writer.writerow(["put_rho", f"{g['put_rho']:.10f}"])
    writer.writerow([])

    writer.writerow([
        "offset",
        "strike",
        "call_price",
        "put_price",
        "call_delta",
        "put_delta",
        "gamma",
        "vega",
        "call_theta",
        "put_theta",
        "call_rho",
        "put_rho",
    ])
    for row in results["rows"]:
        writer.writerow([
            row["label"],
            f"{row['strike']:.10f}",
            f"{row['call']:.10f}",
            f"{row['put']:.10f}",
            f"{row['call_delta']:.10f}",
            f"{row['put_delta']:.10f}",
            f"{row['gamma']:.10f}",
            f"{row['vega']:.10f}",
            f"{row['call_theta']:.10f}",
            f"{row['put_theta']:.10f}",
            f"{row['call_rho']:.10f}",
            f"{row['put_rho']:.10f}",
        ])

    csv_data = output.getvalue()
    filename = f"spx_option_pricer_{form['valuation_date']}_{form['expiry_date']}.csv"
    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=False)
