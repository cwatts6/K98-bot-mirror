import asyncio

import event_cache as ec


def print_summary():
    print(
        "Before: last_refreshed =",
        ec.get_last_refreshed(),
        "events_in_memory =",
        len(ec.get_all_upcoming_events()),
    )


async def do_refresh():
    print_summary()
    res = await ec.refresh_event_cache()
    print("Refresh result: events_count =", res)
    print(
        "After: last_refreshed =",
        ec.get_last_refreshed(),
        "events_in_memory =",
        len(ec.get_all_upcoming_events()),
    )
    # Print first few events if any
    evs = ec.get_all_upcoming_events()
    if evs:
        print("First parsed events (up to 10):")
        for e in evs[:10]:
            st = e.get("start_time")
            st_iso = getattr(st, "isoformat", lambda: str(st))()
            print(" -", st_iso, "|", e.get("type"), "|", e.get("name"))
    else:
        print("No events parsed (in-memory list is empty).")


if __name__ == "__main__":
    asyncio.run(do_refresh())
