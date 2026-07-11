from django.shortcuts import redirect
from functools import wraps

def role_required(view_func):
    """
    Decorator for views that checks that the user is logged in and has a role assigned,
    redirecting to the pending-role page if necessary.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # 1. First, check if they are even logged in
        if not request.user.is_authenticated:
            return redirect('signin')
        
        # 2. Check if the user has a role (role is not None)
        if not request.user.role:
            return redirect('pending_role')
            
        # 3. If they have a role, let them proceed to the view
        return view_func(request, *args, **kwargs)
        
    return _wrapped_view