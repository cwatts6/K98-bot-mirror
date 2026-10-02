from __future__ import annotations

import asyncio
import math

from constants import _conn
from target_utils import _name_cache, sync_refresh_worker


async def _count_view_rows() -> int:
    def _run() -> int:
        with _conn() as cn:
            cur = cn.cursor()
            cur.execute("SELECT COUNT(1) FROM dbo.vw_All_Governors_Clean")
            return int(cur.fetchone()[0])

    return await asyncio.to_thread(_run)


def _is_missing(val) -> bool:
    if val is None:
        return True
    try:
        return math.isnan(float(val))
    except Exception:
        return False


async def main() -> None:
    # In-process refresh so _name_cache is populated in THIS process
    await asyncio.to_thread(sync_refresh_worker)

    rows = _name_cache.get("rows", [])
    if not rows:
        view_count = await _count_view_rows()
        raise RuntimeError(
            f"name_cache rows is empty after refresh. vw_All_Governors_Clean rows={view_count}."
        )

    with_ch = [r for r in rows if not _is_missing(r.get("CityHallLevel"))]
    missing = len(rows) - len(with_ch)

    print(f"Total rows: {len(rows)}")
    print(f"Rows with CityHallLevel: {len(with_ch)}")
    print(f"Rows missing CityHallLevel: {missing}")

    if not with_ch:
        raise RuntimeError("CityHallLevel is missing from all cached rows.")

    # Distribution preview
    dist = {}
    for r in with_ch:
        ch = int(float(r["CityHallLevel"]))
        dist[ch] = dist.get(ch, 0) + 1
    top = sorted(dist.items(), key=lambda x: x[1], reverse=True)[:10]
    print("CityHallLevel distribution (top 10):")
    for ch, count in top:
        print(f"  CH{ch}: {count}")


if __name__ == "__main__":
    asyncio.run(main())
