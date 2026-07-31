from datetime import datetime
from main.models import (
    tbl_cmf_dates, tbl_cmf_formula, tbl_cmf_pending_completed,
)

def get_export_data(date_from, date_to, include_completed, include_pending, include_rs):
    """
    Builds the two datasets needed for the export preview/download:
    - pending_rows: CMF (and optionally RS) records with status == Pending
    - completed_rows: CMF (and optionally RS) records with status == Completed
    Filtered by date range against each record's "date form was made".
    """
    def parse_date(d_str):
        if not d_str:
            return None
        try:
            return datetime.strptime(d_str.strip(), '%m/%d/%Y').date()
        except ValueError:
            return None

    date_from_parsed = parse_date(date_from)
    date_to_parsed = parse_date(date_to)

    pending_rows = []
    completed_rows = []

    # --- CMF records ---
    status_records = tbl_cmf_pending_completed.objects.filter(
        cm_no__isnull=False
    ).select_related('cm_no', 'cm_no__sm', 'code')

    for entry in status_records:
        cmf = entry.cm_no
        formula = tbl_cmf_formula.objects.filter(cm_no=cmf.cm_no).first()
        dates = tbl_cmf_dates.objects.filter(cm_no=cmf.cm_no).first()

        form_made = dates.form_made if dates else None
        if date_from_parsed and (not form_made or form_made < date_from_parsed):
            continue
        if date_to_parsed and (not form_made or form_made > date_to_parsed):
            continue

        prod_code = entry.code.product_code if entry.code else "---"

        if entry.is_completed:
            if not include_completed:
                continue
            completed_rows.append({
                "customer": formula.customer if formula else "---",
                "code": prod_code,
                "date_request": dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "---",
                "date_lab_received": dates.date_received_lab if dates else "---",
                "date_submitted": entry.date_submitted.strftime('%m/%d/%Y') if entry.date_submitted else "---",
                "ar_no": entry.ar_no or "---",
                "ar_date": entry.ar_date.strftime('%m/%d/%Y') if entry.ar_date else "---",
            })
        else:
            if not include_pending:
                continue
            pending_rows.append({
                "matching_no": cmf.cm_no,
                "customer": formula.customer if formula else "---",
                "date_form_made": dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "---",
                "date_lab_received": dates.date_received_lab if dates else "---",
                "date_needed": dates.date_required if dates else "---",
                "target_date": f"due on {dates.due_date_lab.strftime('%m/%d/%y')}" if dates and dates.due_date_lab else "---",
                "end_product": formula.finished_product if formula else "---",
                "color": cmf.color_desc or "---",
                "matching_type": cmf.matching_type or "---",
                "sm": cmf.sm.name if cmf.sm else "---",
                "reason": entry.reason or "pending",
            })

    # --- RS records (only if include_rs is checked) ---
    if include_rs:
        rs_status_records = tbl_cmf_pending_completed.objects.filter(
            rs_no__isnull=False
        ).select_related('rs_no', 'rs_no__sm_no', 'code')

        for entry in rs_status_records:
            rs = entry.rs_no
            dates = tbl_cmf_dates.objects.filter(rs_no=rs).first()

            form_made = dates.form_made if dates else None
            if date_from_parsed and (not form_made or form_made < date_from_parsed):
                continue
            if date_to_parsed and (not form_made or form_made > date_to_parsed):
                continue

            prod_code = entry.code.product_code if entry.code else "---"

            if entry.is_completed:
                if not include_completed:
                    continue
                completed_rows.append({
                    "customer": rs.customer or "---",
                    "code": prod_code,
                    "date_request": dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "---",
                    "date_lab_received": dates.date_received_lab if dates else "---",
                    "date_submitted": entry.date_submitted.strftime('%m/%d/%Y') if entry.date_submitted else "---",
                    "ar_no": entry.ar_no or "---",
                    "ar_date": entry.ar_date.strftime('%m/%d/%Y') if entry.ar_date else "---",
                })
            else:
                if not include_pending:
                    continue
                pending_rows.append({
                    "matching_no": rs.rs_no,
                    "customer": rs.customer or "---",
                    "date_form_made": dates.form_made.strftime('%m/%d/%Y') if dates and dates.form_made else "---",
                    "date_lab_received": dates.date_received_lab if dates else "---",
                    "date_needed": dates.date_required if dates else "---",
                    "target_date": f"due on {dates.due_date_lab.strftime('%m/%d/%y')}" if dates and dates.due_date_lab else "---",
                    "end_product": rs.finished_product or "---",
                    "color": rs.color_desc or "---",
                    "matching_type": rs.matching_type or "---",
                    "sm": rs.sm_no.name if rs.sm_no else "---",
                    "reason": entry.reason or "pending",
                })

    return pending_rows, completed_rows