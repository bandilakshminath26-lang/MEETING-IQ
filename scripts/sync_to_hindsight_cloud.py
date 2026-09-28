"""Idempotent sync of core customer memories to Hindsight Cloud.

Usage:
    python scripts/sync_to_hindsight_cloud.py
"""

from __future__ import annotations
import asyncio
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.config import get_settings
from app.db.database import async_session_factory
from app.db.models.models import HindsightMemory
from sqlalchemy import select
import httpx

settings = get_settings()


async def sync_customer_memories(customer_ids: list[str] | None = None, batch_size: int = 5):
    """Sync memories for the specified customers into Hindsight Cloud."""
    if not settings.hindsight_api_key or settings.hindsight_api_key in ("your_hindsight_api_key_here", "placeholder"):
        print("[ERROR] Hindsight API key is not configured. Aborting sync.")
        return

    base_url = settings.hindsight_base_url.rstrip("/")
    bank_id = settings.hindsight_memory_bank_id
    headers = {
        "Authorization": f"Bearer {settings.hindsight_api_key}",
        "Content-Type": "application/json",
    }

    # Ensure bank exists
    async with httpx.AsyncClient(timeout=30.0) as client:
        r_bank = await client.put(f"{base_url}/v1/default/banks/{bank_id}", headers=headers, json={"name": bank_id})
        print(f"[1/3] Hindsight Bank check: HTTP {r_bank.status_code}")

    # Fetch memories from DB
    async with async_session_factory() as session:
        stmt = select(HindsightMemory)
        if customer_ids:
            stmt = stmt.where(HindsightMemory.customer_id.in_(customer_ids))
        stmt = stmt.order_by(HindsightMemory.id)
        result = await session.execute(stmt)
        memories = result.scalars().all()

    print(f"[2/3] Retrieved {len(memories)} memories to sync for customers: {customer_ids or 'ALL'}")

    # Batch retain
    total_retained = 0
    async with httpx.AsyncClient(timeout=45.0) as client:
        for i in range(0, len(memories), batch_size):
            chunk = memories[i : i + batch_size]
            items = []
            for m in chunk:
                tags = []
                if m.customer_id:
                    tags.append(str(m.customer_id))
                if m.contact_id:
                    tags.append(str(m.contact_id))
                if m.event_type:
                    tags.append(str(m.event_type))

                safe_meta = {}
                if m.metadata_json and isinstance(m.metadata_json, dict):
                    for k, v in m.metadata_json.items():
                        if v is not None:
                            safe_meta[str(k)] = str(v)

                items.append({
                    "content": m.content,
                    "context": str(m.event_type or m.source or "meeting"),
                    "metadata": safe_meta,
                    "tags": tags,
                    "timestamp": str(m.event_date) if m.event_date else None,
                })

            try:
                resp = await client.post(
                    f"{base_url}/v1/default/banks/{bank_id}/memories",
                    headers=headers,
                    json={"items": items},
                )
                if resp.status_code in (200, 201):
                    total_retained += len(items)
                    print(f"  [OK] Batch {i // batch_size + 1}: retained {len(items)} items (total: {total_retained})")
                else:
                    print(f"  [WARN] Batch {i // batch_size + 1} status {resp.status_code}: {resp.text[:120]}")
            except Exception as e:
                print(f"  [ERROR] Batch {i // batch_size + 1} error: {e}")

            await asyncio.sleep(0.3)

    print(f"\n[3/3] Sync complete: {total_retained} memories successfully retained in Hindsight Cloud!")


if __name__ == "__main__":
    # Primary focus on flagship demo customer C001 (NexaCloud) and C002 (BioGen)
    targets = ["C001", "C002"]
    if len(sys.argv) > 1:
        targets = sys.argv[1].split(",")
    asyncio.run(sync_customer_memories(targets))
