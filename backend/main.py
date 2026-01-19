from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import math
import os
import json
import asyncio
import pandas as pd

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/audit/{ticker}")
async def get_audit(ticker: str):
    try:
        # Use .upper() to ensure consistency
        symbol = ticker.upper()
        # Add .NS if not present for Indian stocks
        yf_ticker = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        price = info.get("currentPrice", 0)
        
        # --- YOUR ORIGINAL LOGIC (Unchanged) ---
        f_score = 0
        if info.get("trailingEps", 0) > 0: f_score += 1
        if info.get("returnOnAssets", 0) > 0: f_score += 1
        if info.get("operatingCashflow", 0) > 0: f_score += 1
        if info.get("operatingCashflow", 0) > info.get("netIncomeToCommon", 0): f_score += 1
        if info.get("debtToEquity", 100) < 100: f_score += 1
        if info.get("currentRatio", 0) > 1: f_score += 1
        f_score += 1 
        if info.get("grossMargins", 0) > 0.20: f_score += 1
        if info.get("returnOnEquity", 0) > 0.15: f_score += 1

        eps = info.get("trailingEps", 0)
        bvps = info.get("bookValue", 0)
        graham_no = math.sqrt(22.5 * eps * bvps) if eps > 0 and bvps > 0 else 0
        mos = ((graham_no - price) / graham_no) * 100 if graham_no > 0 else -100

        if f_score >= 7:
            if mos > 10:
                verdict, advice = "PRIME_VALUE", "RARE BARGAIN: High safety & low price. Strong Buy signal."
            else:
                verdict, advice = "QUALITY_GROWTH", "EXPENSIVE LEADER: Elite health, but wait for a price dip."
        elif f_score <= 3:
            verdict, advice = "RISK_TRAP", "DANGER: Failing financials. Do not buy regardless of price."
        else:
            verdict, advice = "NEUTRAL_HOLD", "AVERAGE: No clear edge. Better opportunities exist elsewhere."

        return {
            "status": "success",
            "ticker": symbol,
            "company": info.get("longName", symbol),
            "price": price,
            "f_score": f_score,
            "mos": round(mos, 1),
            "verdict": verdict,
            "advice": advice,
            "graham": round(graham_no, 2)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- NEW AUTOMATION LOGIC FOR GITHUB ---

async def run_daily_bulk_audit():
    """Automatically fetches NSE list and runs your audit on all of them"""
    print("Fetching live NSE ticker list...")
    try:
        # This gets the official list of all stocks on the NSE
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        tickers = df['SYMBOL'].head(50).tolist() # Start with top 50 to test speed
    except:
        tickers = ["RELIANCE", "TCS", "INFY", "HDFCBANK"] # Fallback
    
    final_results = []
    for t in tickers:
        print(f"Auditing {t}...")
        res = await get_audit(t)
        if res["status"] == "success":
            final_results.append(res)
    
    # Save to a file so GitHub can commit it
    with open("daily_audit_results.json", "w") as f:
        json.dump(final_results, f, indent=4)
    print("Daily Audit Complete. File Saved.")

if __name__ == "__main__":
    # Check if we are on GitHub or your Local PC
    if os.getenv("GITHUB_ACTIONS") == "true":
        # On GitHub: Run the audit and then STOP
        asyncio.run(run_daily_bulk_audit())
    else:
        # On Local PC: Start the server for your Frontend
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)