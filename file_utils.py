# file_utils.py
import csv
from datetime import datetime
from io import StringIO

import aiofiles


async def append_csv_line(file_path, values):
    """Appends a line to a CSV file asynchronously."""
    line = ",".join(str(v).replace(",", " ") for v in values) + "\n"
    async with aiofiles.open(file_path, mode="a", encoding="utf-8") as f:
        await f.write(line)


async def log_embed_to_file(embed):
    """Logs an embed title and description to a text file asynchronously."""
    async with aiofiles.open("embed_audit.log", "a", encoding="utf-8") as f:
        await f.write(f"[{datetime.utcnow().isoformat()}] {embed.title} - {embed.description}\n")


async def read_summary_log_rows(summary_log_path):
    async with aiofiles.open(summary_log_path, encoding="utf-8") as f:
        contents = await f.read()
    return list(csv.DictReader(StringIO(contents)))
