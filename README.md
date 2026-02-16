# S&P 500 Option Pricer Web App

A small Flask web app to price European call/put options with Black–Scholes.

## Features

- Inputs:
  - Valuation date (default: today)
  - Expiry date (default: one month from today)
  - Current price and strike (default: ATM based on latest S&P 500 `^GSPC`)
  - Volatility (default: latest VIX `^VIX`, as %)
  - Risk-free rate (default: latest 13-week T-bill proxy `^IRX`, as %)
- Calculates:
  - ATM call and put values
  - Adjacent strikes at `-10%`, `-5%`, `+0%`, `+5%`, `+10%`

## Deploy (Render)

This repo includes `render.yaml` for easy deployment on Render.

1. Go to Render dashboard and choose **New +** → **Blueprint**.
2. Connect this GitHub repo: `sim8n-cpu/spx-option-pricer-webapp`.
3. Render will detect `render.yaml` and deploy automatically.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open: http://127.0.0.1:8080

## Tests

```bash
PYTHONPATH=. pytest -q
```

## Notes

- This uses Black–Scholes (European style assumptions).
- `^IRX` is used as an online proxy for risk-free rate.
- Market-data calls have fallback defaults if an API request fails.
