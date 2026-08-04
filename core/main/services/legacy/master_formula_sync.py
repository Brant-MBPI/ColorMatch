import collections
import dbfread
from django.db import connection
from .dbf_utils import to_bool, to_float, to_int, to_str, is_valid_date, dbf_path

def sync_master_formula(progress_callback=None):
    """
    Mirrors master formula records from DBF into PostgreSQL.
    """
    def emit(msg):
        if progress_callback:
            progress_callback(msg)

    emit("Master Formula: reading items (tbl_formula04)...")
    items_by_uid = collections.defaultdict(list)
    dbf_f_items = dbfread.DBF(dbf_path('master_formula_items'), encoding='latin1', char_decode_errors='ignore')
    
    for item in dbf_f_items:
        uid = to_int(item.get('T_UID'))
        if uid is None:
            continue
        items_by_uid[uid].append({
            "uid": uid, 
            "seq": to_int(item.get('T_SEQ')),
            "material_code": to_str(item.get('T_MATCODE')),
            "concentration": to_float(item.get('T_CON')),
            "is_deleted": to_bool(item.get('T_DELETED')),
        })

    emit("Master Formula: reading primary records (tbl_formula03)...")
    primary_recs = []
    dbf_primary = dbfread.DBF(dbf_path('master_formula_primary'), encoding='latin1', char_decode_errors='ignore')
    
    for r in dbf_primary:
        uid = to_int(r.get('T_UID'))
        if uid is None:
            continue
            
        primary_recs.append({
            "uid": uid, 
            "index_no": to_str(r.get('T_INDEX')),
            "date": r.get('T_DATE'), 
            "customer": to_str(r.get('T_CUSTOMER')),
            "prod_code": to_str(r.get('T_PRODCODE')), 
            "prod_color": to_str(r.get('T_PRODCOLO')),
            "dosage": to_float(r.get('T_DOSAGE')), 
            "ld": to_float(r.get('T_LD')),
            "total_concentration": to_float(r.get('T_TOTALCON')), 
            "mix_time": to_str(r.get('T_MIX')),
            "resin": to_str(r.get('T_RESIN')), 
            "application": to_str(r.get('T_APP')),
            "cm_no": to_str(r.get('T_CMNUM')),
            "cm_date": r.get('T_CMDATE') if is_valid_date(r.get('T_CMDATE')) else None,
            "notes": to_str(r.get('T_REM')), 
            "date_time": to_str(r.get('T_UDATE')),
            "is_deleted": to_bool(r.get('T_DELETED')), 
            "is_used": to_bool(r.get('T_USED')),
            "html": to_str(r.get('T_HTML')), # Hex code
            "cyan": to_float(r.get('T_C')),
            "magenta": to_float(r.get('T_M')),
            "yellow": to_float(r.get('T_Y')),
            "black": to_float(r.get('T_K')),
            "matched_by": to_str(r.get('T_MATCHBY')), 
            "encoded_by": to_str(r.get('T_ENCODEB')),
            "updated_by": to_str(r.get('T_UPDATEBY')),
        })

    if not primary_recs:
        emit("Master Formula: no records found.")
        return 0

    emit("Master Formula: writing to PostgreSQL...")
    with connection.cursor() as cursor:
        # 1. Update Primary Table
        cursor.executemany("""
            INSERT INTO tbl_master_formula (
                form_id, index_no, date, customer, product_code, prod_color, 
                dosage, total_concentration, ld, mix_time, resin, application, 
                cm_no, colormatch_date, notes, date_time, is_deleted, is_used,
                html_code_hex, cyan, magenta, yellow, black
            )
            VALUES (
                %(uid)s, %(index_no)s, %(date)s, %(customer)s, %(prod_code)s, %(prod_color)s, 
                %(dosage)s, %(total_concentration)s, %(ld)s, %(mix_time)s, %(resin)s, %(application)s, 
                %(cm_no)s, %(cm_date)s, %(notes)s, %(date_time)s, %(is_deleted)s, %(is_used)s,
                %(html)s, %(cyan)s, %(magenta)s, %(yellow)s, %(black)s
            )
            ON CONFLICT (form_id) DO UPDATE SET 
                customer=EXCLUDED.customer, 
                is_deleted=EXCLUDED.is_deleted, 
                is_used=EXCLUDED.is_used, 
                notes=EXCLUDED.notes,
                html_code_hex=EXCLUDED.html_code_hex,
                cyan=EXCLUDED.cyan,
                magenta=EXCLUDED.magenta,
                yellow=EXCLUDED.yellow,
                black=EXCLUDED.black;
        """, primary_recs)

        uids = tuple(r['uid'] for r in primary_recs)

        # 2. Update Encode Table
        cursor.execute("DELETE FROM tbl_master_formula_encode WHERE form_id IN %s", [uids])
        cursor.executemany("""
            INSERT INTO tbl_master_formula_encode (form_id, match_by, encoded_by, updated_by) 
            VALUES (%(uid)s, %(matched_by)s, %(encoded_by)s, %(updated_by)s)
        """, primary_recs)

        # 3. Update Items Table
        cursor.execute("DELETE FROM tbl_master_formula_info WHERE form_id IN %s", [uids])
        all_items = [i for r in primary_recs for i in items_by_uid.get(r['uid'], [])]
        if all_items:
            cursor.executemany("""
                INSERT INTO tbl_master_formula_info (form_id, sequence_no, material_code, concentration, is_deleted) 
                VALUES (%(uid)s, %(seq)s, %(material_code)s, %(concentration)s, %(is_deleted)s)
            """, all_items)

    emit(f"Master Formula: synced {len(primary_recs)} primary records.")
    return len(primary_recs)