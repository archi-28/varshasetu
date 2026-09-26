# VarshaSetu

**Monsoon risk exploration and agricultural advisory** — an interactive Streamlit prototype for the Meerut district of Uttar Pradesh.

> VarshaSetu is a demonstration tool. Its bundled weather history is synthetic; forecasts and advisories are examples, not operational guidance. Use official forecasts and local agricultural expertise for real decisions.

## What it does

- Shows a district dashboard with block-level sample forecasts and risk markers.
- Explores rainfall and climate-index history in charts.
- Displays model metrics and the model's feature-importance diagnostics.
- Generates sample crop guidance and English/Hindi alert text.
- Runs from its included demo dataset without external data services or credentials.

All displayed records are synthetic demonstration data. Map markers are representative points and are not official administrative boundaries. Model probabilities are not calibrated or validated for operational use.

## Run locally

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
streamlit run app.py
```

Linux/macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On first start, VarshaSetu generates the synthetic sample and trains its demo model if needed. To regenerate the sample manually, run `python scripts/generate_demo_data.py`.

## Share on Streamlit Community Cloud

1. Push this project to a GitHub repository.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) and choose **Create app**.
3. Select the repository, branch, and `app.py` as the app file.
4. Deploy. No API keys or external data downloads are required.

## Docker

```bash
docker build -t varshasetu .
docker run --rm -p 8501:8501 varshasetu
```

Or run `docker compose up --build`.

## Project layout

- `app.py` — Streamlit interface
- `config.yaml` — app name, Meerut blocks, paths, and prototype thresholds
- `data/sample/` — synthetic demo weather data
- `src/` — loading, features, forecasts, risk, advisory, alerts, and map modules
- `scripts/` — demo generation, training, evaluation, and optional ingestion utility
- `tests/` — project checks

## Limitations

- Synthetic data does not represent observed weather or establish forecast skill.
- The map uses illustrative points; it does not show official block shapes.
- Classifier probabilities are not calibrated for operational decisions.
- The displayed extended horizons and advisory rules are prototype demonstrations.
- Farmer alert generation only creates local sample text; it does not send messages.

VarshaSetu is not an official meteorological service and must not replace official forecasts or qualified agricultural advice.

