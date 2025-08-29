import csv
from pathlib import Path
from decimal import Decimal

CSV_FILE = Path("history.csv")

if not CSV_FILE.exists():
    print("No history.csv found. Run buy_the_dip.py at least once first.")
    exit()

print("========== TRADE HISTORY ==========")

total_usdt = Decimal("0")
total_btc = Decimal("0")
total_fee_btc = Decimal("0")

with open(CSV_FILE, mode="r", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

    if not rows:
        print("No trades recorded yet.")
    else:
        for row in rows:
            print("-----------------------------------")
            print(f"Datetime   : {row['datetime_utc']}")
            print(f"Action     : {row['action']}")
            print(f"Symbol     : {row['symbol']}")
            print(f"Base Amt   : {row['base_amount_usdt']} USDT")
            print(f"BTC Bought : {row['btc_qty']} (avg price {row['avg_price']} USDT)")
            print(f"Fee        : {row['fee']}")
            print(f"Dip Order  : {row['dip_qty']} BTC @ {row['dip_price']}")
            print(f"USDT Bal   : {row['usdt_before']} -> {row['usdt_after']}")
            print(f"BTC Bal    : {row['btc_before']} -> {row['btc_after']}")

            # accumulate totals
            try:
                total_usdt += Decimal(row['base_amount_usdt'])
                total_btc += Decimal(row['btc_qty'])
                total_fee_btc += Decimal(row['fee'])
            except Exception:
                pass

print("===================================")
print("========== TOTAL SUMMARY ==========")
print(f"Total USDT invested : {total_usdt}")
print(f"Total BTC bought    : {total_btc}")
print(f"Total fees (BTC)    : {total_fee_btc}")
if total_btc > 0:
    avg_price_all = total_usdt / total_btc
    print(f"Average buy price   : {avg_price_all:.2f} USDT")
print("===================================")
