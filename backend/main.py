from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import math
import os
import json
import asyncio
import pandas as pd
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/audit/{ticker}")
async def get_audit(ticker: str):
    try:
        symbol = ticker.upper()
        yf_ticker = f"{symbol}.NS" if not symbol.endswith(".NS") else symbol
        
        stock = yf.Ticker(yf_ticker)
        info = stock.info
        hist = stock.history(period="1mo") 
        
        price = info.get("currentPrice", 0)
        
        sector = info.get("sector", "Unknown")
        volume = info.get("volume", 0)
        mcap = info.get("marketCap", 0)
        pe = info.get("trailingPE", 0)
        sec_pe = info.get("forwardPE", pe * 1.1) 

        high = hist['High'].max()
        low = hist['Low'].min()
        close = hist['Close'].iloc[-1]
        
        pivot = (high + low + close) / 3
        res1 = (2 * pivot) - low
        sup1 = (2 * pivot) - high

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
            verdict, advice = ("PRIME VALUE", "RARE BARGAIN: High safety & low price.") if mos > 10 else ("QUALITY_GROWTH", "EXPENSIVE LEADER: Elite health.")
        elif f_score <= 3:
            verdict, advice = "RISK TRAP", "DANGER: Failing financials."
        else:
            verdict, advice = "NEUTRAL HOLD", "AVERAGE: No clear edge."

        return {
            "status": "success",
            "ticker": symbol,
            "company": info.get("longName", symbol),
            "price": round(price, 2),
            "sector": sector,
            "volume": f"{volume/1000000:.1f}M",
            "mcap": f"{mcap/10000000:.0f}Cr",
            "pe": round(pe, 1),
            "sec_pe": round(sec_pe, 1),
            "f_score": f_score,
            "mos": round(mos, 1),
            "verdict": verdict,
            "advice": advice,
            "graham": round(graham_no, 2),
            "short_res": round(res1, 2),
            "short_piv": round(pivot, 2),
            "short_sup": round(sup1, 2),
            "long_res": round(res1 * 1.05, 2),
            "long_piv": round(pivot * 1.02, 2),
            "long_sup": round(sup1 * 0.98, 2)
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

async def run_daily_bulk_audit():
    print("Fetching live NSE ticker list...")
    try:
        url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
        df = pd.read_csv(url)
        tickers = sorted(df['SYMBOL'].dropna().unique().tolist())
    except:
        tickers = ["RELIANCE", "TCS", "INFY"]

    filename = "daily_audit_results.json"
    
    # 1. Initialize file with an open bracket and a newline
    with open(filename, "w") as f:
        f.write("[\n")

    first_entry = True
    successful_count = 0

    for i, t in enumerate(tickers):
        try:
            res = await get_audit(t)
            if res["status"] == "success":
                with open(filename, "a") as f:
                    if not first_entry:
                        f.write(",")
                    
                    # Minify individual records
                    json.dump(res, f, separators=(',', ':'))
                    
                    # 2. Add a newline every 10 records to keep file readable and Git-friendly
                    successful_count += 1
                    if successful_count % 10 == 0:
                        f.write("\n")
                
                print(f"[{i+1}/{len(tickers)}] SAVED: {t}")
                first_entry = False
            
            if i % 12 == 0: time.sleep(1) # Slight adjustment for rate limiting

        except Exception as e:
            print(f"Error on {t}: {e}")
            continue

    # 3. Close the JSON array
    with open(filename, "a") as f:
        f.write("\n]")
    
    print(f"Full audit complete. {successful_count} stocks saved.")

if __name__ == "__main__":
    if os.getenv("GITHUB_ACTIONS") == "true":
        asyncio.run(run_daily_bulk_audit())
    else:
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=8000)