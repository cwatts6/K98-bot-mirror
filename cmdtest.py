import psutil

print("=== Running Process Inspection ===")
for proc in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        name = proc.info["name"]
        cmdline = proc.info["cmdline"]
        if not cmdline:
            continue

        if any("python" in name.lower() for name in [name] + cmdline):
            print(f"\n[PID {proc.pid}] {name}")
            print("CMDLINE:", cmdline)
    except Exception:
        continue
