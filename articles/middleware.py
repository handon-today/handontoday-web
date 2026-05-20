from django.core.cache import cache
from django.http import HttpResponseForbidden


class HoneypotMiddleware:
    """Honeypot에 걸린 IP 차단 미들웨어"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = request.META.get('HTTP_X_FORWARDED_FOR', request.META.get('REMOTE_ADDR', ''))
        if ip:
            ip = ip.split(',')[0].strip()
            if cache.get(f'honeypot_blocked_{ip}'):
                return HttpResponseForbidden('403 Forbidden')

        return self.get_response(request)
