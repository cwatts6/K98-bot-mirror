# probe_event_parsing.py — run inside same python env as the bot
import asyncio

import event_data_loader as ed


async def probe():
    for key, rng in ed.RANGES.items():
        print("=== RANGE", key, rng)
        raw = ed._fetch_values(rng)
        print(" raw rows:", None if raw is None else len(raw))
        if raw:
            print("  raw sample:", raw[:3])
            if key in ("ruins", "altar"):
                parsed = ed.parse_event_dates(raw, label=key, etype=key)
            elif key == "major":
                parsed = ed.parse_major_dates(raw)
            else:
                parsed = ed.parse_chronicle_dates(raw)
            print("  parsed count (future-only):", len(parsed))
            for e in parsed[:10]:
                st = e.get("start_time")
                print(
                    "   parsed:",
                    getattr(st, "isoformat", lambda: str(st))(),
                    "name:",
                    e.get("name"),
                )
            # show first few dropped: compare raw->all parsed before filtering
            # (quick ad-hoc: parse into all without _sorted_future_only)
            all_events = []
            try:
                for row in raw:
                    try:
                        st = ed._parse_dt_str_utc(str(row[0]))
                        all_events.append(st.isoformat())
                    except Exception as ex:
                        all_events.append(f"<bad:{ex}>")
                print("  first parsed (all, not future-filtered):", all_events[:10])
            except Exception:
                pass


asyncio.run(probe())
