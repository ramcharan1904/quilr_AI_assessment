def authorized(role, method, params):
    # Only tools/call is gated (admin_* tools require the admin role). Every other
    # method - tools/list, initialize, ping, resources/list, etc. - is forwarded
    # transparently; this gateway does not restrict the rest of the protocol surface.
    if method != "tools/call":
        return True
    name = params.get("name", "")
    if isinstance(name, str) and name.startswith("admin_"):
        return role == "admin"
    return True
