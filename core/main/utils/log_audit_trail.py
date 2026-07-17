from ..models import tbl_audit_trail

def log_audit(request, action, details):
    """
    Reusable function to record user actions.
    Usage: log_audit(request, "Saved", "Saved CMF No A9123a")
    """
    try:
        tbl_audit_trail.objects.create(
            user=request.user, 
            action_type=action,
            details=details
        )
    except Exception as e:
        # We print the error so it doesn't crash the main app if logging fails
        print(f"Audit Log Error: {e}")