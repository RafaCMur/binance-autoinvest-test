import csv
from pathlib import Path
from datetime import datetime, timezone

CSV_FILE = Path("history.csv")

def log_trade(action, symbol, base_amount, btc_qty, price, fee, dip_price=None, dip_qty=None, base_before=None, base_after=None, btc_before=None, btc_after=None, base_currency="EUR"):
    """
    Append a row to history.csv with all relevant data
    """
    # create file with headers if not exists
    if not CSV_FILE.exists():
        with open(CSV_FILE, mode="w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "datetime_utc", "action", "symbol", "base_currency",
                "base_amount", "btc_qty", "avg_price", "fee",
                "dip_price", "dip_qty",
                "base_before", "base_after", "btc_before", "btc_after"
            ])

    # write new row
    with open(CSV_FILE, mode="a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            datetime.now(timezone.utc).isoformat(),
            action, symbol, base_currency,
            base_amount, btc_qty, price, fee,
            dip_price, dip_qty,
            base_before, base_after, btc_before, btc_after
        ])
