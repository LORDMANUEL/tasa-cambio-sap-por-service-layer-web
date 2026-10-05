from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]


def test_readme_verified_binary_block_uses_one_release_version():
    text = (ROOT / "README.md").read_text(encoding="utf-8")

    match = re.search(
        r"## Binarios V(?P<version>\d+\.\d+\.\d+) verificados\n(?P<section>.*?)(?=\n## Release estable)",
        text,
        re.S,
    )
    assert match, "README must contain the verified binaries section"

    version = match.group("version")
    section = match.group("section")

    expected = (
        f"Atas-V{version}-Setup-x64.exe",
        f"Atas-V{version}-Portable-x64.zip",
        f"atas_{version}_amd64.deb",
        f"docs/RELEASE_MANIFEST_V{version}.md",
    )
    for value in expected:
        assert value in section, f"README verified-binaries block is inconsistent: missing {value}"


def test_readme_release_test_count_matches_test_report():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    report = (ROOT / "TEST_REPORT.md").read_text(encoding="utf-8")

    readme_count = re.search(r"con \*\*(\d+) pruebas automáticas por plataforma\*\*", readme)
    report_count = re.search(r"- `pytest`: \*\*(\d+) passed\*\*", report)

    assert readme_count and report_count
    assert readme_count.group(1) == report_count.group(1)
