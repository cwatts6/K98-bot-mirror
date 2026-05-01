# Lightweight module to expose a module-level trigger for log backup so it can be run
# in an isolated subprocess (importable as log_backup:trigger_log_backup_sync).
import logging
import os
import time

try:
    import pyodbc
except Exception:
    pyodbc = None

logger = logging.getLogger(__name__)


def trigger_log_backup_sync(job_name: str = "ROK_TRACKER - LOG Backup") -> dict:
    """
    Wrapper moved out of DL_bot so it can be invoked via subprocess as log_backup:trigger_log_backup_sync.
    Implementation mirrors the existing logic from DL_bot._trigger_log_backup_sync.
    """
    server = os.environ.get("SQL_MONITOR_SERVER") or os.environ.get("SQL_SERVER") or None
    msdb_database = "msdb"
    username = (
        os.environ.get("SQL_MONITOR_USERNAME")
        or os.environ.get("IMPORT_USERNAME")
        or os.environ.get("SQL_USERNAME")
    )
    password = (
        os.environ.get("SQL_MONITOR_PASSWORD")
        or os.environ.get("IMPORT_PASSWORD")
        or os.environ.get("SQL_PASSWORD")
    )

    job_id_env = os.environ.get("SQL_MONITOR_JOB_ID")

    if not (server and username and password):
        logger.warning("Log backup trigger skipped: missing DB credentials.")
        return {"ok": False, "error": "missing_db_credentials"}

    if pyodbc is None:
        logger.warning(
            "pyodbc not available in environment; cannot trigger log backup programmatically."
        )
        return {"ok": False, "error": "pyodbc_missing"}

    conn_str = (
        f"DRIVER={{ODBC Driver 17 for SQL Server}};"
        f"SERVER={server};DATABASE={msdb_database};UID={username};PWD={password};"
    )
    conn = None
    try:
        conn = pyodbc.connect(conn_str, autocommit=True)
        cur = conn.cursor()

        tried_methods = []
        used_method = None
        triggered = False
        err_messages = []

        # 1) Preferred: call wrapper
        try:
            cur.execute("EXEC dbo.usp_start_rok_tracker_log_backup;")
            logger.info("Requested msdb.dbo.usp_start_rok_tracker_log_backup successfully.")
            tried_methods.append("wrapper")
            used_method = "wrapper"
            triggered = True
        except Exception as werr:
            logger.info("Wrapper call failed or not present: %s", werr)
            tried_methods.append("wrapper_failed")
            err_messages.append(f"wrapper:{werr}")

        # 2) job_id
        if not triggered and job_id_env:
            try:
                cur.execute("EXEC msdb.dbo.sp_start_job @job_id = ?", job_id_env)
                logger.info("Requested SQL Agent job by id %s", job_id_env)
                tried_methods.append("job_id")
                used_method = "job_id"
                triggered = True
            except Exception as e:
                logger.warning("sp_start_job by id failed: %s", e)
                tried_methods.append("job_id_failed")
                err_messages.append(f"job_id:{e}")

        # 3) job_name
        if not triggered:
            try:
                cur.execute("EXEC msdb.dbo.sp_start_job @job_name = ?", job_name)
                logger.info("Requested SQL Agent job by name '%s'", job_name)
                tried_methods.append("job_name")
                used_method = "job_name"
                triggered = True
            except Exception as e:
                logger.warning("sp_start_job by name failed: %s", e)
                tried_methods.append("job_name_failed")
                err_messages.append(f"job_name:{e}")

        # 4) ad-hoc backup
        if not triggered:
            try:
                backup_dir = os.environ.get("SQL_BACKUP_DIR", r"C:\SQL_BACKUP\LOG")
                try:
                    os.makedirs(backup_dir, exist_ok=True)
                except Exception:
                    pass
                timestamp = int(time.time())
                backup_file = os.path.join(backup_dir, f"ROK_TRACKER_log_trigger_{timestamp}.trn")
                cur.execute(
                    "BACKUP LOG [ROK_TRACKER] TO DISK = ? WITH INIT, COMPRESSION", (backup_file,)
                )
                logger.info("Performed ad-hoc BACKUP LOG to %s", backup_file)
                tried_methods.append("ad_hoc_backup_log")
                used_method = "ad_hoc_backup_log"
                triggered = True
            except Exception as e2:
                logger.warning("Ad-hoc BACKUP LOG failed: %s", e2)
                tried_methods.append("ad_hoc_failed")
                err_messages.append(f"ad_hoc:{e2}")

        diagnostics = {
            "method_tried": tried_methods,
            "used_method": used_method,
            "last_log_backup": None,
            "log_reuse_wait_desc": None,
            "log_space_used_pct": None,
        }

        # Post-trigger diagnostics (best-effort)
        try:
            cur.execute(
                "SELECT TOP 1 backup_finish_date FROM msdb.dbo.backupset WHERE database_name = 'ROK_TRACKER' AND type = 'L' ORDER BY backup_finish_date DESC"
            )
            row = cur.fetchone()
            if row:
                diagnostics["last_log_backup"] = row[0]
            cur.execute("SELECT log_reuse_wait_desc FROM sys.databases WHERE name = 'ROK_TRACKER'")
            row = cur.fetchone()
            if row:
                diagnostics["log_reuse_wait_desc"] = row[0]
            try:
                cur.execute("DBCC SQLPERF(LOGSPACE)")
                rows = cur.fetchall()
                for r in rows:
                    try:
                        name = str(r[0])
                    except Exception:
                        name = None
                    if name and name.upper() == "ROK_TRACKER":
                        try:
                            diagnostics["log_space_used_pct"] = float(r[2])
                        except Exception:
                            diagnostics["log_space_used_pct"] = None
                        break
            except Exception:
                logger.debug(
                    "DBCC SQLPERF(LOGSPACE) failed during post-trigger check", exc_info=True
                )
        except Exception:
            logger.exception("Failed to collect post-trigger diagnostics", exc_info=True)

        if triggered:
            reuse = diagnostics.get("log_reuse_wait_desc")
            pct = diagnostics.get("log_space_used_pct")

            # RELAXED CHECK: Only fail if log usage is STILL high AND reuse wait persists
            # (reuse_wait can lag behind the actual backup completion)
            if reuse and str(reuse).upper() not in ("NOTHING", ""):
                # Check if log percentage actually dropped
                if pct is not None and pct > 80.0:
                    logger.warning(
                        "Log backup trigger executed (method=%s) but log still high: reuse=%s pct=%.2f%%",
                        used_method,
                        reuse,
                        pct,
                    )
                    return {"ok": False, "error": "reuse_wait_persists_high_usage", **diagnostics}
                else:
                    # Log usage is acceptable - consider it success even if reuse_wait lags
                    logger.info(
                        "Log backup triggered successfully (method=%s); reuse_wait=%s but log usage acceptable (%.2f%%)",
                        used_method,
                        reuse,
                        pct or 0,
                    )
                    return {"ok": True, **diagnostics}

            logger.info("Log backup trigger executed successfully; diagnostics=%s", diagnostics)
            return {"ok": True, **diagnostics}
        else:
            logger.warning("All log backup trigger attempts failed: %s", err_messages)
            return {"ok": False, "error": "trigger_failed", "errors": err_messages, **diagnostics}

    except Exception as conn_err:
        logger.warning("Failed to connect for log backup trigger: %s", conn_err)
        return {"ok": False, "error": f"connect_failed:{conn_err}"}
    finally:
        try:
            if conn:
                conn.close()
        except Exception:
            pass
