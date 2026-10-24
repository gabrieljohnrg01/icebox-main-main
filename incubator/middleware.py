from django.shortcuts import redirect
from django.urls import resolve

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if not request.user.has_usable_password() or request.user.must_change_password:
                current_url_name = resolve(request.path_info).url_name
                if current_url_name not in ['set_password', 'logout']:
                    return redirect('set_password')

        response = self.get_response(request)
        return response
