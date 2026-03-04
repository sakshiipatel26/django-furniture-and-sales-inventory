from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.urls import reverse

class CustomerOnlyMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of paths that don't require authentication
        public_paths = ['/', '/about/', '/categories/', '/product/', '/login/', '/register/']
        
        # Allow access to static and media files
        if request.path.startswith(('/static/', '/media/')):
            return self.get_response(request)

        # Check if accessing admin site
        if request.path.startswith('/admin/'):
            if request.user.is_authenticated and not request.user.is_staff:
                logout(request)
                messages.error(request, 'Please login with admin credentials')
                return redirect('admin:login')
            return self.get_response(request)

        # Check if accessing main site
        if request.user.is_authenticated:
            try:
                if request.user.userprofile.user_type != 'customer':
                    logout(request)
                    messages.error(request, 'Please login as customer')
                    return redirect('login')
            except:
                pass

        # Allow public paths
        if any(request.path.startswith(path) for path in public_paths):
            return self.get_response(request)

        return self.get_response(request)