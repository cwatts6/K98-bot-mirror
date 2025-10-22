#!/usr/bin/env python3
"""
scripts/collect_diagnostics.py

Collects runtime artifacts and optionally uploads the resulting tar.gz to S3 or an artifact HTTP endpoint.

Usage examples:
  # Collect only (writes archive locally)
  python scripts/collect_diagnostics.py -o /tmp/k98-diagnostics.tar.gz

  # Collect and upload to S3 (uses boto3 / AWS credentials from env or role)
  python scripts/collect_diagnostics.py --include-logs --upload --s3-bucket my-bucket --s3-prefix diagnostics/k98/

  # Collect and upload to HTTP artifact endpoint
  python scripts/collect_diagnostics.py --upload --artifact-url https://artifacts.example.com/upload --artifact-token "TOKEN"
"""
from __future__ import annotations

import argparse
from collections.abc import Iterable
import datetime
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile

# Safe imports of repo constants (fallback to sane defaults)
try:
    # Importing constants.py should be cheap and safe
    from constants import (
        BOT_LOCK_PATH,
        COMMAND_CACHE_FILE,
        DATA_DIR,
        LOG_DIR,
        QUEUE_CACHE_FILE,
    )
except Exception:
    LOG_DIR = os.environ.get("LOG_DIR", "logs")
    DATA_DIR = os.environ.get("DATA_DIR", "data")
    QUEUE_CACHE_FILE = os.path.join(DATA_DIR, "live_queue_cache.json")
    COMMAND_CACHE_FILE = os.path.join(DATA_DIR, "command_cache.json")
    BOT_LOCK_PATH = os.path.join(DATA_DIR, "BOT_LOCK.json")


def mask_value(k: str, v: str) -> str:
    """Redact sensitive env values while keeping some context."""
    if v is None:
        return ""
    key = k.upper()
    sensitive_keywords = ("TOKEN", "SECRET", "KEY", "PASS", "CRED", "CREDENTIAL", "GOOGLE")
    if any(term in key for term in sensitive_keywords):
        if len(v) <= 8:
            return "REDACTED"
        return f"{v[:4]}...{v[-4:]}"
    return v


def dump_env(path: Path) -> None:
    env_path = path / "env.txt"
    with env_path.open("w", encoding="utf-8") as f:
        f.write("# Environment snapshot (sensitive values redacted)\n")
        for k, v in sorted(os.environ.items()):
            try:
                f.write(f"{k}={mask_value(k, v)}\n")
            except Exception:
                f.write(f"{k}=<error reading value>\n")


def tail_lines(path: Path, max_lines: int = 2000) -> list[str]:
    """Return the last max_lines lines from path efficiently."""
    if not path.exists():
        return []
    # Efficient tail: read blocks from end as bytes, then decode once
    lines_bytes: list[bytes] = []
    with path.open("rb") as f:
        f.seek(0, os.SEEK_END)
        file_size = f.tell()
        block_size = 4096
        blocks: list[bytes] = []
        remaining = file_size
        while remaining > 0 and len(lines_bytes) <= max_lines:
            read_size = min(block_size, remaining)
            f.seek(remaining - read_size)
            data = f.read(read_size)
            blocks.append(data)
            remaining -= read_size
            chunk = b"".join(reversed(blocks))
            try:
                lines_bytes = chunk.splitlines()
            except Exception:
                f.seek(0)
                lines_bytes = f.read().splitlines()
                break
    decoded = [ln.decode("utf-8", "replace") for ln in lines_bytes[-max_lines:]]
    return decoded


def head_lines(path: Path, max_lines: int = 200) -> list[str]:
    if not path.exists():
        return []
    with path.open("rb") as f:
        lines: list[str] = []
        for _ in range(max_lines):
            ln = f.readline()
            if not ln:
                break
            lines.append(ln.decode("utf-8", "replace"))
    return lines


def safe_copy(src: Path, dst: Path) -> None:
    try:
        shutil.copy2(src, dst)
    except Exception as e:
        with dst.with_suffix(dst.suffix + ".error").open("w", encoding="utf-8") as f:
            f.write(f"Failed to copy {src}: {e}\n")


def collect_service_status(service: str | None, out: Path) -> None:
    if not service:
        return
    try:
        proc = subprocess.run(
            ["systemctl", "status", service], capture_output=True, text=True, timeout=8
        )
        (out / f"systemctl_{service}.txt").write_text(
            f"returncode={proc.returncode}\n\nSTDOUT:\n{proc.stdout}\n\nSTDERR:\n{proc.stderr}\n",
            encoding="utf-8",
        )
    except FileNotFoundError:
        (out / "systemctl_not_found.txt").write_text("systemctl not available on this host\n")
    except Exception as e:
        (out / "systemctl_error.txt").write_text(f"error calling systemctl: {e}\n")


def try_psutil(out: Path) -> None:
    try:
        # psutil may not be installed on all hosts; silence static-checker import with type ignore
        import psutil  # type: ignore

        info = {}
        p = psutil.Process()
        info["pid"] = p.pid
        info["cmdline"] = p.cmdline()
        info["cwd"] = p.cwd()
        try:
            info["memory_info"] = p.memory_info()._asdict()
        except Exception:
            info["memory_info"] = None
        try:
            info["cpu_times"] = p.cpu_times()._asdict()
        except Exception:
            info["cpu_times"] = None
        try:
            info["open_files"] = [f.path for f in p.open_files()]
        except Exception:
            info["open_files"] = []
        (out / "psutil_process.json").write_text(json.dumps(info, indent=2), encoding="utf-8")
    except Exception as e:
        (out / "psutil_error.txt").write_text(f"psutil not available or failed: {e}\n")


def collect_basic_system_info(out: Path) -> None:
    python_exec = shutil.which("python") or "python"
    info = {
        "timestamp_utc": datetime.datetime.utcnow().isoformat() + "Z",
        "platform": os.uname() if hasattr(os, "uname") else ("platform_unavailable",),
        "cwd": os.getcwd(),
        "user": os.getenv("USER") or os.getenv("USERNAME"),
        "python": {"executable": python_exec},
    }
    (out / "system_info.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


def upload_to_s3(archive_path: Path, bucket: str, prefix: str | None = None) -> str:
    """
    Upload to S3 using boto3. Returns the S3 key (path) of the uploaded object.
    Raises RuntimeError on missing boto3 or upload failure.
    """
    try:
        import boto3  # type: ignore
    except Exception as e:
        raise RuntimeError("boto3 is required for S3 uploads but is not installed") from e

    s3 = boto3.client("s3")
    key_prefix = prefix or ""
    if key_prefix and not key_prefix.endswith("/"):
        key_prefix = key_prefix + "/"
    key = f"{key_prefix}{archive_path.name}"
    try:
        s3.upload_file(str(archive_path), bucket, key)
    except Exception as e:
        raise RuntimeError(f"S3 upload failed: {e}") from e
    # Construct an S3 URL (note: bucket may be private; this is a convenience string)
    return f"s3://{bucket}/{key}"


def upload_to_http(archive_path: Path, url: str, token: str | None = None) -> str:
    """
    Upload to a generic artifact endpoint via multipart/form-data POST.
    Returns the remote URL or server response text.
    Requires the 'requests' library.
    """
    try:
        import requests  # type: ignore
    except Exception as e:
        raise RuntimeError("requests is required for HTTP uploads but is not installed") from e

    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    files = {"file": (archive_path.name, archive_path.open("rb"), "application/gzip")}
    try:
        resp = requests.post(url, headers=headers, files=files, timeout=60)
        resp.raise_for_status()
    except Exception as e:
        raise RuntimeError(f"HTTP upload failed: {e}") from e
    # Attempt to return an informative URL from JSON or plain text
    try:
        data = resp.json()
        # common field checks
        for key in ("url", "artifact_url", "location"):
            if key in data:
                return str(data[key])
        return json.dumps(data)
    except Exception:
        return resp.text


def gather(
    output: str | None,
    include_logs: bool,
    service: str | None,
    max_tail: int,
    extra_paths: Iterable[str],
) -> str:
    ts = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
    default_name = f"k98-diagnostics-{ts}"
    tmpdir = Path(tempfile.mkdtemp(prefix=default_name + "-"))
    files_dir = tmpdir / "files"
    meta_dir = tmpdir / "meta"
    files_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    errors: list[str] = []

    # 1) Dump environment (redacted)
    try:
        dump_env(meta_dir)
    except Exception as e:
        errors.append(f"env dump failed: {e}")

    # 2) Collect configured repo artifacts
    try:
        log_dir = Path(LOG_DIR)
        candidates = {
            "log.txt": log_dir / "log.txt",
            "error_log.txt": log_dir / "error_log.txt",
            "crash.log": log_dir / "crash.log",
            "heartbeat.json": log_dir / "heartbeat.json",
        }
        for name, path in candidates.items():
            if path.exists():
                if include_logs:
                    safe_copy(path, files_dir / name)
                head = head_lines(path, max_lines=250)
                tail = tail_lines(path, max_lines=max_tail)
                (meta_dir / (name + ".head.txt")).write_text("".join(head), encoding="utf-8")
                (meta_dir / (name + ".tail.txt")).write_text("".join(tail), encoding="utf-8")
    except Exception as e:
        errors.append(f"log collection failed: {e}")

    # 3) Data dir artifacts (queue/command cache, last shutdown info, lock file)
    try:
        data_files = {
            Path(QUEUE_CACHE_FILE).name: Path(QUEUE_CACHE_FILE),
            Path(COMMAND_CACHE_FILE).name: Path(COMMAND_CACHE_FILE),
            "BOT_LOCK": Path(BOT_LOCK_PATH),
        }
        possible_last_shutdown = Path(DATA_DIR) / "LAST_SHUTDOWN_INFO.json"
        data_files["LAST_SHUTDOWN_INFO.json"] = possible_last_shutdown
        for name, path in data_files.items():
            if path.exists():
                safe_copy(path, files_dir / name)
    except Exception as e:
        errors.append(f"data collection failed: {e}")

    # 4) Extra provided paths (absolute or relative)
    for p in extra_paths:
        path = Path(p)
        if path.exists():
            try:
                if path.is_dir():
                    dst = files_dir / path.name
                    shutil.copytree(path, dst)
                else:
                    safe_copy(path, files_dir / path.name)
            except Exception as e:
                errors.append(f"extra path {p} copy failed: {e}")
        else:
            errors.append(f"extra path {p} not found")

    # 5) systemctl status if requested
    try:
        collect_service_status(service, meta_dir)
    except Exception as e:
        errors.append(f"systemctl collection failed: {e}")

    # 6) psutil diagnostics (optional)
    try:
        try_psutil(meta_dir)
    except Exception as e:
        errors.append(f"psutil collection failed: {e}")

    # 7) basic system info
    try:
        collect_basic_system_info(meta_dir)
    except Exception as e:
        errors.append(f"system info failed: {e}")

    # 8) write errors summary if any
    if errors:
        (meta_dir / "errors.txt").write_text("\n".join(errors), encoding="utf-8")

    # 9) create archive
    out_path = Path(output) if output else Path.cwd() / (default_name + ".tar.gz")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with tarfile.open(out_path, "w:gz") as tar:
        for item in files_dir.iterdir():
            tar.add(item, arcname=f"files/{item.name}")
        for item in meta_dir.iterdir():
            tar.add(item, arcname=f"meta/{item.name}")

    try:
        shutil.rmtree(tmpdir)
    except Exception:
        pass

    return str(out_path)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Collect runtime diagnostics for the K98 bot and produce a tar.gz archive."
    )
    p.add_argument(
        "--output",
        "-o",
        help="Path to output archive (tar.gz). Default: ./k98-diagnostics-<ts>.tar.gz",
    )
    p.add_argument(
        "--include-logs",
        action="store_true",
        help="Include whole log files in the archive (may be large). Head+Tail always included.",
    )
    p.add_argument(
        "--service",
        help="systemd service name to gather status for (e.g. k98-bot).",
        default=None,
    )
    p.add_argument(
        "--max-tail",
        type=int,
        default=2000,
        help="Number of tail lines to capture from large logs (default: 2000).",
    )
    p.add_argument(
        "--extra",
        nargs="*",
        default=[],
        help="Extra file or directory paths to include in the archive.",
    )
    # Upload options
    p.add_argument(
        "--upload",
        action="store_true",
        help="Upload the produced archive to configured destination (S3 or artifact URL).",
    )
    p.add_argument(
        "--s3-bucket", help="S3 bucket name for upload (overrides DIAGNOSTICS_S3_BUCKET env)."
    )
    p.add_argument(
        "--s3-prefix", help="S3 key prefix (optional; overrides DIAGNOSTICS_S3_PREFIX env)."
    )
    p.add_argument(
        "--artifact-url",
        help="Artifact HTTP upload endpoint URL (overrides ARTIFACT_UPLOAD_URL env).",
    )
    p.add_argument(
        "--artifact-token",
        help="Artifact upload token (overrides ARTIFACT_UPLOAD_TOKEN env).",
    )
    return p.parse_args()


def main() -> None:
    args = parse_args()
    print("Collecting diagnostics... this may take a few seconds.")
    archive = gather(args.output, args.include_logs, args.service, args.max_tail, args.extra)
    print(f"Diagnostics archive created: {archive}")

    if args.upload:
        # Determine configuration from CLI or environment
        s3_bucket = args.s3_bucket or os.environ.get("DIAGNOSTICS_S3_BUCKET")
        s3_prefix = args.s3_prefix or os.environ.get("DIAGNOSTICS_S3_PREFIX")
        artifact_url = args.artifact_url or os.environ.get("ARTIFACT_UPLOAD_URL")
        artifact_token = args.artifact_token or os.environ.get("ARTIFACT_UPLOAD_TOKEN")

        uploaded_locations = []
        last_error = None

        if s3_bucket:
            print(f"Attempting S3 upload to bucket: {s3_bucket} (prefix={s3_prefix})")
            try:
                s3_loc = upload_to_s3(Path(archive), s3_bucket, s3_prefix)
                uploaded_locations.append(s3_loc)
                print(f"S3 upload successful: {s3_loc}")
            except Exception as e:
                last_error = e
                print(f"S3 upload failed: {e}")

        if artifact_url:
            print(f"Attempting HTTP upload to: {artifact_url}")
            try:
                url_or_resp = upload_to_http(Path(archive), artifact_url, artifact_token)
                uploaded_locations.append(url_or_resp)
                print(f"HTTP upload successful: {url_or_resp}")
            except Exception as e:
                last_error = e
                print(f"HTTP upload failed: {e}")

        if not uploaded_locations:
            print("No upload succeeded.")
            if last_error:
                raise SystemExit(1) from last_error
    else:
        print("Upload not requested; finished.")


if __name__ == "__main__":
    main()
