from datetime import datetime
import re
# Helpers
def to_bool(val):
    if val == 'Y': return True
    if val == 'N': return False
    return None

def format_date(d_str):
    if not d_str or d_str.upper() == "ASAP": return None
    try:
        return datetime.strptime(d_str.split(',')[0].strip(), '%m/%d/%Y').strftime('%Y-%m-%d')
    except: return None

def clean_numeric(val):
    if not val: return "0"
    return re.sub(r'[^\d.]', '', str(val))