from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]


def test_proprietary_license_and_legal_notices_exist():
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    legal = (ROOT / "LEGAL.md").read_text(encoding="utf-8")
    security = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    third = (ROOT / "THIRD_PARTY_NOTICES.md").read_text(encoding="utf-8")

    assert "PERSONAL PROPRIETARY SOFTWARE LICENSE" in license_text
    assert "Copyright © 2026 Luis Manuel Fajardo Rivera" in license_text
    assert "NOT OPEN SOURCE" in license_text
    assert "NO WARRANTY" in license_text
    assert "LIMITATION OF LIABILITY" in license_text
    assert "SAP SE" in legal
    assert "127.0.0.1" in security
    assert "requirements-runtime.txt" in third


def test_github_pages_points_to_stable_v503_assets():
    site = (ROOT / "site/index.html").read_text(encoding="utf-8")
    expected = (
        "Atas-V5.0.3-Setup-x64.exe",
        "Atas-V5.0.3-Portable-x64.zip",
        "atas_5.0.3_amd64.deb",
    )
    for name in expected:
        assert name in site
    assert "releases/download/v5.0.2/" not in site
    assert "V5.0.2" not in site


def test_public_docs_do_not_claim_sap_affiliation():
    docs = "\n".join(
        [
            (ROOT / "README.md").read_text(encoding="utf-8"),
            (ROOT / "LEGAL.md").read_text(encoding="utf-8"),
            (ROOT / "site/index.html").read_text(encoding="utf-8"),
        ]
    ).lower()
    prohibited = (
        "official sap product",
        "certified by sap",
        "endorsed by sap",
        "producto oficial de sap",
    )
    for phrase in prohibited:
        assert phrase not in docs
