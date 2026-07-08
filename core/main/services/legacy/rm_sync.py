import dbfread
from django.db import connection

from .dbf_utils import to_bool, to_str, is_valid_date, dbf_path


def sync_rm_list(progress_callback=None):
    """
    Rebuilds tbl_raw_material_list from the RM warehouse DBF (full truncate + reinsert).
    Returns the number of unique RM codes synced.
    """
    def emit(msg):
        if progress_callback:
            progress_callback(msg)

    emit("RM List: reading raw material warehouse file...")
    unique_rm_codes = set()
    dbf = dbfread.DBF(dbf_path('rm_wh'), encoding='latin1', char_decode_errors='ignore')
    for r in dbf:
        code = to_str(r.get('T_MATCODE'))
        if to_bool(r.get('T_DELETED')) or not code:
            continue
        unique_rm_codes.add(code)

    data = [{"rm_code": code} for code in unique_rm_codes]

    emit("RM List: writing to PostgreSQL...")
    with connection.cursor() as cursor:
        cursor.execute("TRUNCATE TABLE tbl_raw_material_list RESTART IDENTITY CASCADE")
        cursor.executemany("INSERT INTO tbl_raw_material_list (rm_code) VALUES (%(rm_code)s)", data)

    emit(f"RM List: synced {len(data)} unique codes.")
    return len(data)


def sync_rm_incoming(progress_callback=None):
    """
    Mirrors the latest incoming record per material code into tbl_rm_incoming.
    Returns the number of records synced.
    """
    def emit(msg):
        if progress_callback:
            progress_callback(msg)

    emit("RM Incoming: reading incoming file...")
    dbf = dbfread.DBF(dbf_path('rm_incoming'), encoding='latin1', char_decode_errors='ignore')
    latest_by_code = {}
    for r in dbf:
        if to_bool(r.get('T_DELETED')):
            continue
        mat_code = to_str(r.get('T_MATCODE'))
        if not mat_code:
            continue
        raw_date = r.get('T_DATE')
        valid = is_valid_date(raw_date)
        existing = latest_by_code.get(mat_code)
        if existing is None or (valid and (not existing['date'] or raw_date > existing['date'])):
            latest_by_code[mat_code] = {
                "material_code": mat_code,
                "note": to_str(r.get('T_NOTE')),
                "date": raw_date if valid else None,
            }

    if not latest_by_code:
        emit("RM Incoming: no records found.")
        return 0

    data = list(latest_by_code.values())

    emit("RM Incoming: writing to PostgreSQL...")
    with connection.cursor() as cursor:
        cursor.executemany("""
            INSERT INTO tbl_rm_incoming (date, material_code, note)
            VALUES (%(date)s, %(material_code)s, %(note)s)
            ON CONFLICT (material_code) DO UPDATE SET note = EXCLUDED.note, date = EXCLUDED.date
        """, data)

    emit(f"RM Incoming: synced {len(data)} records.")
    return len(data)