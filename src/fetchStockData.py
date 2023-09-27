import yfinance as yf
# Request historical data for past 5 years
data = yf.Ticker("NVDA").history(period='1m')
# Show info
print(data.info())