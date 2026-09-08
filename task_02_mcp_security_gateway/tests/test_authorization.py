from app.authorization import authorized

def test_viewer_list():
    assert authorized("viewer", "tools/list", {})

def test_viewer_blocked():
    assert not authorized("viewer", "tools/call", {"name": "admin_reset_key"})

def test_admin_allowed():
    assert authorized("admin", "tools/call", {"name": "admin_reset_key"})

def test_viewer_non_admin_tool_call_allowed():
    assert authorized("viewer", "tools/call", {"name": "get_customer_record"})

def test_other_methods_forwarded_by_default():
    assert authorized("viewer", "initialize", {})
    assert authorized("viewer", "ping", {})
