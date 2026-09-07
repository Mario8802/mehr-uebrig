def no_client_ip(request):
    """Username-based lockout: do not store or trust proxy-supplied client IPs."""
    return None
