class OrganizationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        def get_organization():
            if not hasattr(request, "_organization"):
                if request.user.is_authenticated:
                    staff_profile = getattr(request.user, 'staff', None)
                    request._organization = staff_profile.organization if staff_profile else None
                else:
                    request._organization = None
            return request._organization

        request.get_organization = lambda : get_organization()
        return self.get_response(request)
