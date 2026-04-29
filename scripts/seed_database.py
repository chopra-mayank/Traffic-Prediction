from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.database import init_db
from backend.services.data_loader import seed_bangalore_readings


if __name__ == "__main__":
    init_db()
    count = seed_bangalore_readings()
    print(f"Database ready. Seeded or detected {count} Bangalore traffic rows.")
