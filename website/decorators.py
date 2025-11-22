from django.shortcuts import redirect
from functools import wraps


def teacher_required(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and hasattr(user, 'teacherprofile'):
            return view_func(request, *args, **kwargs)

        return redirect('home')
    return _wrapped_view


def student_required(view_func):

    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = request.user
        if user.is_authenticated and hasattr(user, 'studentprofile'):
            return view_func(request, *args, **kwargs)

        return redirect('home')
    return _wrapped_view
