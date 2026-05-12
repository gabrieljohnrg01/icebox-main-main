from django.shortcuts import redirect
from django.urls import resolve

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Check if user has an unusable password
            if not request.user.has_usable_password():
                # Allow access to the set_password and logout views
                current_url_name = resolve(request.path_info).url_name
                if current_url_name not in ['set_password', 'logout']:
                    return redirect('set_password')

        response = self.get_response(request)
        return response
