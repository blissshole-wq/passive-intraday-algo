import time

try:
    import yfinance as yf
except Exception:  # pragma: no cover - environment-dependent
    yf = None

WATCHLIST = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS",
             "BHARTIARTL.NS", "SBIN.NS", "ITC.NS", "HINDUNILVR.NS", "LT.NS"]


def main():
    if yf is None:
        print("Trading test stub: yfinance is not installed, so no market data will be fetched.")
        return

    print("🚀 Trading test active...")
    for ticker in WATCHLIST:
        try:
            hist = yf.Ticker(ticker).history(period="1mo", interval="1d")
            if hist.empty:
                continue
            price = float(hist['Close'].iloc[-1])
            print(f"{ticker}: {price}")
        except Exception as exc:
            print(f"Error fetching {ticker}: {exc}")
        time.sleep(0.1)


if __name__ == "__main__":
    main()