import pytest
from src.core.discovery.shadow_it_scanner import ShadowITScanner

def test_shadow_it_detection():
    scanner = ShadowITScanner()

    # Report a new unknown asset
    scanner.report_asset("10.0.0.5", 5432, "PostgreSQL")

    unauthorized = scanner.get_unauthorized_assets()
    assert len(unauthorized) == 1
    assert unauthorized[0].ip == "10.0.0.5"
    assert unauthorized[0].status == "unauthorized"

def test_shadow_it_authorization():
    scanner = ShadowITScanner()

    # Pre-authorize
    scanner.authorize_asset("10.0.0.6", 80)

    # Report asset
    scanner.report_asset("10.0.0.6", 80, "Nginx")

    unauthorized = scanner.get_unauthorized_assets()
    assert len(unauthorized) == 0

    # Verify it is in known assets but authorized
    key = "10.0.0.6:80"
    assert scanner.known_assets[key].status == "authorized"
