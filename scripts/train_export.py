from __future__ import annotations

import json
import os
import sys
from datetime import datetime
from pathlib import Path

import joblib


BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

PROCESSED_CSV = BASE_DIR / "data" / "processed" / "traffic_clean.csv"
MODEL_DIR = BASE_DIR / "backend" / "saved_models"


def main() -> None:
    MODEL_DIR.mkdir(parents=True, exist_ok=True)
    model_path = MODEL_DIR / "xgboost_model.pkl"
    force = os.getenv("FORCE_PLACEHOLDER_MODEL", "").lower() in {"1", "true", "yes"}

    if model_path.exists() and not force:
        print(
            "Existing xgboost_model.pkl found. Skipping placeholder generation so a real Colab-trained model is not overwritten."
        )
        return

    placeholder = {
        "message": "Train in Google Colab using notebooks/03_model_training_colab.ipynb and replace this artifact.",
        "processed_csv_exists": PROCESSED_CSV.exists(),
        "created_at": datetime.utcnow().isoformat(),
    }
    with (MODEL_DIR / "model_metadata.json").open("w", encoding="utf-8") as handle:
        json.dump(placeholder, handle, indent=2)
    joblib.dump(placeholder, model_path)
    print("Placeholder artifacts created. Replace them with Colab-trained exports.")


if __name__ == "__main__":
    main()
