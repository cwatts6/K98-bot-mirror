# file_utils.py
import csv
from datetime import datetime
import io
from io import StringIO

import aiofiles


async def append_csv_line(file_path, values):
    """Appends a line to a CSV file asynchronously using proper escaping."""
    # Use csv.writer to ensure proper CSV quoting/escaping, then write buffer to file asynchronously
    buf = io.StringIO()
    writer = csv.writer(buf)
    # Convert values to strings in a consistent way (None -> empty string)
    safe_values = ["" if v is None else v for v in values]
    writer.writerow(safe_values)
    async with aiofiles.open(file_path, mode="a", encoding="utf-8", newline="") as f:
        await f.write(buf.getvalue())


async def log_embed_to_file(embed):
    """Logs an embed title and description to a text file asynchronously."""
    # Defer importing utcnow to avoid circular import at module import time
    try:
        from utils import utcnow as _utcnow
    except Exception:
        _utcnow = None

    ts = _utcnow().isoformat() if _utcnow else datetime.utcnow().isoformat()
    async with aiofiles.open("embed_audit.log", "a", encoding="utf-8") as f:
        await f.write(f"[{ts}] {embed.title} - {embed.description}\n")


async def read_summary_log_rows(summary_log_path):
    async with aiofiles.open(summary_log_path, encoding="utf-8") as f:
        contents = await f.read()
    return list(csv.DictReader(StringIO(contents)))
