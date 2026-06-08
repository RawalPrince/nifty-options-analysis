# 📈 NIFTY Options Expiry Analysis

A data analysis project examining NIFTY weekly options behavior across 30 expiry cycles using real NSE data.

🔴 **[Live Dashboard](https://nifty-options-analysis-dvwytmvckjevqw63nqyuyt.streamlit.app)**

---

## Key Findings

| Analysis | Finding |
|----------|---------|
| Theta Decay | ATM CE premiums lose **61.7%** of value from DTE-15 to DTE-2 |
| Max Pain | NIFTY expires within **0.24%** of max pain level on average |
| PCR Signal | PCR-based signal achieves **61% directional accuracy** across 77 signals |
| IV Behavior | IV **rises** into expiry — spikes in final 2 days (contrary to traditional IV crush) |

---

## Dataset

- **Source:** NSE Archives (official bhavcopy data)
- **Period:** Dec 2024 – May 2025
- **Records:** 202,509 NIFTY options records
- **Expiry cycles:** 30 weekly/monthly expiries
- **Fields:** Strike, OI, Volume, IV Proxy, Underlying Price, CE/PE

---

## Project Structure
---

## Analysis Modules

### 1. Theta Decay Analysis
- Tracks ATM option premium decay from DTE-15 to expiry
- Separates CE and PE decay curves
- Identifies acceleration zone in final 2 days

### 2. Max Pain & OI Analysis
- Calculates max pain level for each of 30 expiry cycles
- Compares max pain vs actual NIFTY expiry close
- Color-coded gap visualization (green < 0.2%, orange < 0.5%, red > 0.5%)

### 3. PCR Signal Backtesting
- Daily Put-Call Ratio calculated from OI data
- Contrarian signal: PCR > 1.1 = Bullish, PCR < 0.85 = Bearish
- Backtested against next-day NIFTY direction across 77 signals

### 4. IV Behavior Analysis
- Simplified IV proxy: (Premium / Underlying) × √(365/DTE) × 100
- Tracks IV across DTE-15 to expiry day
- Per-expiry cycle IV comparison

---

## Tech Stack

- **Python 3.10**
- **Pandas / NumPy** — data processing
- **Plotly** — interactive charts
- **Streamlit** — dashboard deployment
- **NSE Archives API** — data source

---

## How to Run Locally

```bash
git clone https://github.com/RawalPrince/nifty-options-analysis.git
cd nifty-options-analysis
pip install -r requirements.txt
streamlit run app.py
```

---

## Author

**Prince Rawal**
B.E. Computer Engineering — LDRP-ITR, Gandhinagar
