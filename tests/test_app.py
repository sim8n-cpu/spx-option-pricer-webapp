from app import app


def test_export_csv_route():
    client = app.test_client()
    r = client.get(
        "/export_csv?valuation_date=2026-02-16&expiry_date=2026-03-16&spot=5000&strike=5000&vol_pct=20&risk_free_pct=4"
    )
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    assert b"offset,strike,call_price,put_price" in r.data
