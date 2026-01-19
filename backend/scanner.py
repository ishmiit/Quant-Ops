import yfinance as yf
import json
import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler

# THE MASTER LIST: Ideally, this should contain all NSE tickers from an EQUITY_L.csv
TICKER_SAMPLE = ["RELIANCE.NS", "TCS.NS", "HDFCBANK.NS", "INFY.NS", "ICICIBANK.NS"]

def update_sector_medians():
    print("LOG: Starting Daily Sector Scan...")
    sector_data = {}
    
    for ticker in TICKER_SAMPLE:
        try:
            stock = yf.Ticker(ticker)
            info = stock.info
            sector = info.get('sector', 'Unknown')
            pe = info.get('trailingPE')
            
            if sector not in sector_data:
                sector_data[sector] = []
            if pe:
                sector_data[sector].append(pe)
        except:
            continue

    # Calculate Medians
    final_stats = {}
    for sector, pes in sector_data.items():
        if pes:
            final_stats[sector] = {"median_pe": round(pd.Series(pes).median(), 2)}

    # Save to local "Memory"
    with open('sector_stats.json', 'w') as f:
        json.dump(final_stats, f)
    print("LOG: Sector Stats Updated Successfully.")

# SCHEDULE: Runs every day at 08:00 AM
scheduler = BlockingScheduler()
scheduler.add_job(update_sector_medians, 'cron', hour=8, minute=0)

if __name__ == "__main__":
    # Run once immediately on start to populate data
    update_sector_medians()
    scheduler.start()