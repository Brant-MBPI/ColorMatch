import os
import datetime
from django.conf import settings


def to_bool(value):
    if value is None: return False
    if isinstance(value, bool): return value
    v_str = str(value).strip().upper()
    return v_str in ('T', '.T.', 'Y', '1', 'TRUE', 'YES')


def to_float(value, default=0.0):
    if value is None: return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def to_int(value, default=None):
    if value is None: return default
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return default


def to_str(value, default=''):
    if value is None: return default
    if isinstance(value, bytes):
        try:
            return value.decode('latin1').replace('\x00', '').strip() or default
        except Exception:
            return default
    return str(value).replace('\x00', '').strip() or default


def is_valid_date(d):
    if d is None: return False
    try:
        if isinstance(d, (datetime.date, datetime.datetime)):
            return d.year >= 1900
        s = str(d).strip()
        return bool(s) and not s.startswith('1899')
    except Exception:
        return False


def dbf_path(key):
    """
    Resolves a DBF file path from settings.DBF_PATHS, joined with settings.DBF_BASE_PATH.
    Expects settings.py to define:
        DBF_BASE_PATH = r'\\system-server\SYSTEM-NEW-OLD'
        DBF_PATHS = {
            'formula_primary': 'tbl_formula01.dbf',
            'formula_items': 'tbl_formula02.dbf',
            'production_primary': 'tbl_prod01.dbf',
            'production_items': 'tbl_prod02.dbf',
            'rm_wh': 'tbl_rm_wh.dbf',
            'rm_incoming': 'tbl_incoming.dbf',
        }
    """
    return os.path.join(settings.DBF_BASE_PATH, settings.DBF_PATHS[key])