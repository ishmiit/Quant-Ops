from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import yfinance as yf
import math

# CREATE THE APP
app = FastAPI()

# CONFIGURE THE BRIDGE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/audit/{ticker}")
async def get_audit(ticker: str):
    try:
        stock = yf.Ticker(f"{ticker.upper()}.NS")
        info = stock.info
        hist = stock.history(period="1mo")
        price = info.get("currentPrice", 0)
        
        # --- [STRICTLY PRESERVED] PIOTROSKI F-SCORE ---
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

        # --- [STRICTLY PRESERVED] GRAHAM VALUATION ---
        eps = info.get("trailingEps", 0)
        bvps = info.get("bookValue", 0)
        graham_no = math.sqrt(22.5 * eps * bvps) if eps > 0 and bvps > 0 else 0
        mos = ((graham_no - price) / graham_no) * 100 if graham_no > 0 else -100

        # --- [NEW] PIVOT POINT CALCULATIONS ---
        if not hist.empty:
            h, l, c = hist.iloc[-1]['High'], hist.iloc[-1]['Low'], hist.iloc[-1]['Close']
            p = (h + l + c) / 3
            short_res, short_sup = (2*p)-l, (2*p)-h
            
            mh, ml = hist['High'].max(), hist['Low'].min()
            mp = (mh + ml + c) / 3
            long_res, long_sup = (2*mp)-ml, (2*mp)-mh
        else:
            p = short_res = short_sup = long_res = long_sup = price

        # --- [NEW] PRECISION NEWS SEARCH (Direct Company Focus) ---
        news_items = []
        try:
            # Using yf.Search to get news specifically mentioning the company
            search_query = f"{info.get('longName', ticker.upper())} stock"
            search = yf.Search(search_query, news_count=4)
            for n in search.news:
                link = n.get('link', '#')
                if not link.startswith('http'): link = f"https://finance.yahoo.com{link}"
                news_items.append({
                    "title": n.get('title', "Company Update"),
                    "link": link,
                    "source": n.get('publisher', "Market Feed")
                })
        except:
            news_items = []

        # --- [STRICTLY PRESERVED] VERDICT ENGINE ---
        if f_score >= 7:
            if mos > 10: verdict, advice = "PRIME VALUE", "STRONG BUY: High safety & low price."
            else: verdict, advice = "QUALITY GROWTH", "EXPENSIVE: Elite health, wait for dip."
        elif f_score <= 3:
            verdict, advice = "RISK TRAP", "DANGER: Failing financials. Stay away."
        else:
            verdict, advice = "NEUTRAL HOLD", "AVERAGE: No clear edge currently."

        return {
            "status": "success",
            "company": info.get("longName", ticker.upper()),
            "sector": info.get("sector", "N/A"),
            "price": round(price, 2),
            "f_score": f_score,
            "mos": round(mos, 1),
            "verdict": verdict,
            "advice": advice,
            "pe": round(info.get("trailingPE", 0), 2) if info.get("trailingPE") else "N/A",
            "sec_pe": round(info.get("forwardPE", 25), 2),
            "short_res": round(short_res, 2),
            "short_piv": round(p, 2),
            "short_sup": round(short_sup, 2),
            "long_res": round(long_res, 2),
            "long_piv": round(mp, 2),
            "long_sup": round(long_sup, 2),
            "news": news_items[:3],
            "volume": f"{info.get('regularMarketVolume', 0):,}",
            "mcap": f"{round(info.get('marketCap', 0) / 10000000, 2)} CR"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)