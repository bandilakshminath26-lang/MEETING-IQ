"""Seed the database with the synthetic longitudinal dataset.

Usage:
    python scripts/seed_demo.py
"""

import asyncio
import sys
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == "win32":
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings
from app.db.database import init_db, async_session_factory
from app.ingestion.dataset_loader import load_synthetic_dataset
from app.hindsight.memory_service import get_memory_service


async def main():
    print("=" * 60)
    print("  Meeting Intelligence Agent - Demo Seed")
    print("=" * 60)

    # Initialize database tables
    print("\n[1/3] Initializing database tables...")
    await init_db()
    print("  [OK] Tables created")

    # Load synthetic dataset
    print("\n[2/3] Loading synthetic dataset into PostgreSQL + Hindsight...")
    data_dir = Path(__file__).resolve().parent.parent / "data" / "synthetic"

    async with async_session_factory() as session:
        memory = get_memory_service()
        counts = await load_synthetic_dataset(session, memory, data_dir)
        print(f"  [OK] Loaded: {counts}")

    print("\n[3/3] Seed complete!")
    print("\n  Start the backend:  cd backend && uvicorn app.main:app --reload")
    print("  Start the frontend: cd frontend && npm run dev")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
