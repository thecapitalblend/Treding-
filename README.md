# Jarvis Trading Assistant V3

Streamlit paper-trading research dashboard for Nifty 50.

## Structure

- `app.py` — Streamlit UI
- `core/` — master aggregation, risk and paper journal
- `modules/` — technical, sentiment and celestial engines
- `config.yaml` — settings
- `requirements.txt` — dependencies

## GitHub / Streamlit deployment

Upload the complete folder structure. `app.py`, `config.yaml` and `requirements.txt` stay in the repository root.

After upload, reboot/redeploy the Streamlit app.

## Important

- No real broker orders are sent.
- News and Yahoo Finance data can be unavailable or delayed.
- Celestial calculations are experimental and are not scientifically validated predictors.
- BUY CALL / BUY PUT are directional research signals, not automatic option-contract recommendations.
