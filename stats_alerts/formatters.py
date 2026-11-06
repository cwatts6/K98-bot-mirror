# stats_alerts/formatters.py
import logging
from typing import Any

import numpy as np
import pandas as pd

from embed_utils import fmt_short

logger = logging.getLogger(__name__)


def abbr(n: int | float | None) -> str:
    """Human-friendly compact number representation (delegates to embed_utils.fmt_short)."""
    if n is None:
        return "0"
    try:
        return fmt_short(n)
    except Exception:
        try:
            return str(int(n))
        except Exception:
            return "0"


def fmt_dkp(v: Any, base_dp: int = 2, max_dp: int = 10) -> str:
    """Show DKP with at least base_dp decimals; increase precision if necessary."""
    if v is None:
        return "0.00"
    try:
        val = float(v)
    except Exception:
        return "0.00"

    if val == 0.0:
        return "0.00"

    dp = base_dp
    while dp <= max_dp:
        s = f"{val:.{dp}f}"
        if "." in s and any(ch != "0" for ch in s.split(".", 1)[1]):
            return s
        dp += 1

    s = f"{val:.{max_dp}f}".rstrip("0").rstrip(".")
    return s if s else "0.00"


def fmt_top(
    rows: list[dict],
    name_key: str,
    val_key: str,
    extra_key: str | None = None,
    *,
    val_fmt=None,
    extra_fmt=None,
) -> str:
    """Render 1–3 rows -> numbered list monospaced, with optional per-field formatters."""
    if not rows:
        return "—"
    if val_fmt is None:
        val_fmt = abbr
    if extra_key and extra_fmt is None:
        extra_fmt = abbr

    medals = ["\ud83e\udd47", "\ud83e\udd48", "\ud83e\udd49"]
    out = []
    for i, r in enumerate(rows[:3]):
        left = f"{medals[i]} {r.get(name_key)}"
        right = val_fmt(r.get(val_key))
        if extra_key:
            right += f" | {extra_fmt(r.get(extra_key))}"
        out.append(f"{left} \u2014 `{right}`")
    return "\n".join(out)


def fmt_top_dkp(rows: list[dict], name_key: str, dkp_key: str = "dkp") -> str:
    if not rows:
        return "—"
    medals = ["\ud83e\udd47", "\ud83e\udd48", "\ud83e\udd49"]
    out = []
    for i, r in enumerate(rows[:3]):
        try:
            val = float(r.get(dkp_key, 0))
        except Exception:
            val = 0.0
        out.append(f"{medals[i]} {r.get(name_key)} \u2014 `{val:.2f}`")
    return "\n".join(out)


def fmt_honor(rows: list[dict]) -> str:
    if not rows:
        return "—"
    medals = ["\ud83e\udd47", "\ud83e\udd48", "\ud83e\udd49"]
    lines = []
    for i, r in enumerate(rows[:3]):
        name = r.get("GovernorName") or "Unknown"
        try:
            pts = int(r.get("HonorPoints") or 0)
        except Exception:
            pts = 0
        lines.append(f"{medals[i]} {name} \u2014 `{pts:,}`")
    return "\n".join(lines)


def normalize_row(row_list: list[str]) -> dict | None:
    """Normalize legacy CSV rows into dict(date, time_utc, kind)."""
    parts = [p.strip() for p in row_list if p is not None]
    if len(parts) == 2:
        d, t = parts
        k = "offseason_daily"
    elif len(parts) >= 3:
        d, t, k = parts[0], parts[1], parts[2]
    else:
        return None
    # crude ISO date check
    if len(d) != 10 or d[4] != "-" or d[7] != "-":
        return None
    return {"date": d, "time_utc": t, "kind": k}


def parse_mixed_dates(s: pd.Series) -> pd.Series:
    """Warning-free parsing for mixed inputs (ISO, UK dd/mm/yyyy, Excel serials).

    The previous implementation attempted to call pandas.to_datetime(..., format='mixed')
    which is not a valid parameter. This implementation:
      - Normalizes input
      - Parses numeric values as Excel serials (base 1899-12-30)
      - Attempts a general pd.to_datetime parse (errors='coerce')
      - Retries with dayfirst=True if necessary
      - Falls back to explicit formats
    """
    s = s.astype("object").map(lambda x: x.strip() if isinstance(x, str) else x)
    s = s.replace({"": np.nan, "NULL": np.nan, "NaN": np.nan})

    out = pd.Series(pd.NaT, index=s.index, dtype="datetime64[ns]")

    # Excel serials
    is_num = s.map(lambda x: isinstance(x, (int, float)) and not pd.isna(x))
    if is_num.any():
        serials = s[is_num].astype(float)
        out.loc[is_num] = pd.to_datetime("1899-12-30") + pd.to_timedelta(serials, unit="D")

    # Strings
    str_mask = s.map(lambda x: isinstance(x, str))
    if str_mask.any():
        s_str = s[str_mask]
        # First, let pandas try a general parse (ISO-like and common formats)
        try:
            parsed = pd.to_datetime(s_str, errors="coerce", dayfirst=False)
        except Exception:
            parsed = pd.Series(pd.NaT, index=s_str.index, dtype="datetime64[ns]")

        # If some remain NaT, try dayfirst=True for UK style dates
        still = parsed.isna()
        if still.any():
            try:
                parsed2 = pd.to_datetime(s_str[still], errors="coerce", dayfirst=True)
                parsed.loc[still] = parsed2
            except Exception:
                pass

        # Fall back to explicit formats for any remaining NaT
        still = parsed.isna()
        if still.any():
            for fmt in ("%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d", "%d-%b-%Y", "%d-%b-%y"):
                mask = parsed.isna()
                if not mask.any():
                    break
                try:
                    parsed.loc[mask] = pd.to_datetime(s_str[mask], format=fmt, errors="coerce")
                except Exception:
                    # If parsing with this format fails unexpectedly, continue to the next
                    continue

        out.loc[str_mask] = parsed

    return out


__all__ = [
    "abbr",
    "fmt_dkp",
    "fmt_honor",
    "fmt_top",
    "fmt_top_dkp",
    "normalize_row",
    "parse_mixed_dates",
]
