# users/utils.py
def request_fingerprint(request):
    meta = request.META
    ip = meta.get("HTTP_X_FORWARDED_FOR", meta.get("REMOTE_ADDR", "")).split(",")[0].strip()
    ua = meta.get("HTTP_USER_AGENT", "")
    return ip or None, ua
