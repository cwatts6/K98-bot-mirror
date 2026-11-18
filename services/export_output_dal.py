"""Lossless rows for the existing, explicitly uncoordinated export route."""

from core.export_numeric import sql_output_frame


def read_export_frame(engine, query):
    """Read the existing reviewed query; drain both handles, keeping first failure."""
    connection = engine.raw_connection()
    cursor = None
    first_error = None
    frame = None
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        frame = sql_output_frame(cursor.fetchall(), [c[0] for c in cursor.description])
    except BaseException as exc:
        first_error = exc
    finally:
        for handle in (cursor, connection):
            if handle is not None:
                try:
                    handle.close()
                except BaseException as exc:
                    if first_error is None:
                        first_error = exc
    if first_error is not None:
        raise first_error
    return frame
