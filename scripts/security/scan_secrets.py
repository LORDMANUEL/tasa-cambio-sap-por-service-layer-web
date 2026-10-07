#!/usr/bin/env python3
"""High-confidence secret scanner for the Atas repository and Git history."""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

MAX_BLOB_BYTES=2_000_000
SKIP_SUFFIXES={".png",".jpg",".jpeg",".gif",".webp",".ico",".pdf",".zip",".exe",".deb",".xlsx",".xls",".db",".sqlite",".pyc"}
SKIP_DIRS={".git","dist","build","runtime",".venv","node_modules"}

@dataclass(frozen=True)
class Finding:
    source: str
    rule: str
    snippet: str

RULES=[
    ("private-key",re.compile(r"-----BEGIN (?:RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----")),
    ("github-token",re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    ("github-fine-grained-token",re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b")),
    ("aws-access-key",re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("slack-token",re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,}\b")),
    ("stripe-live-secret",re.compile(r"\bsk_live_[A-Za-z0-9]{16,}\b")),
]
ASSIGNMENT=re.compile(
    r"""(?ix)
    \b(password|passwd|pwd|api[_-]?key|client[_-]?secret|access[_-]?token|auth[_-]?token)
    \s*[:=]\s*
    ["']([^"'\r\n]{8,})["']
    """
)
ALLOW_WORDS=("example","placeholder","changeme","dummy","sample","test-only","not-a-secret","redacted","***")


def _scan_text(source: str, text: str) -> list[Finding]:
    findings=[]
    for name,rx in RULES:
        for match in rx.finditer(text):
            findings.append(Finding(source,name,match.group(0)[:80]))
    normalized=source.replace("\\","/").lower()
    assignment_allowed=normalized.startswith(("tests/","docs/")) or "/tests/" in normalized
    if not assignment_allowed:
        for match in ASSIGNMENT.finditer(text):
            value=match.group(2).strip()
            lower=value.lower()
            if any(word in lower for word in ALLOW_WORDS):
                continue
            findings.append(Finding(source,"literal-secret-assignment",f"{match.group(1)}=<redacted>"))
    return findings


def _decode(data: bytes) -> str | None:
    if b"\x00" in data[:4096]:
        return None
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return data.decode("latin-1")
        except UnicodeDecodeError:
            return None


def scan_worktree(root: Path) -> list[Finding]:
    findings=[]
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel=path.relative_to(root)
        if any(part in SKIP_DIRS for part in rel.parts) or path.suffix.lower() in SKIP_SUFFIXES:
            continue
        if path.stat().st_size>MAX_BLOB_BYTES:
            continue
        text=_decode(path.read_bytes())
        if text is not None:
            findings.extend(_scan_text(rel.as_posix(),text))
    return findings


def _git(*args: str) -> bytes:
    return subprocess.check_output(["git",*args],stderr=subprocess.DEVNULL)


def scan_history() -> list[Finding]:
    findings=[]
    objects=_git("rev-list","--objects","--all").decode("utf-8","replace").splitlines()
    seen=set()
    for line in objects:
        if not line.strip():
            continue
        parts=line.split(" ",1)
        sha=parts[0]
        path=parts[1] if len(parts)>1 else ""
        if sha in seen:
            continue
        seen.add(sha)
        if path and Path(path).suffix.lower() in SKIP_SUFFIXES:
            continue
        try:
            obj_type=_git("cat-file","-t",sha).decode().strip()
            if obj_type!="blob":
                continue
            size=int(_git("cat-file","-s",sha).decode().strip())
            if size>MAX_BLOB_BYTES:
                continue
            data=_git("cat-file","-p",sha)
        except (subprocess.CalledProcessError,ValueError):
            continue
        text=_decode(data)
        if text is not None:
            findings.extend(_scan_text(f"history:{sha[:12]}:{path or '(unknown)'}",text))
    return findings


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--history",action="store_true",help="scan all reachable Git blobs")
    args=parser.parse_args()
    root=Path(__file__).resolve().parents[2]
    findings=scan_worktree(root)
    if args.history:
        findings.extend(scan_history())
    unique={(f.source,f.rule,f.snippet):f for f in findings}
    if unique:
        print("SECRET_SCAN=FAILED")
        for finding in unique.values():
            print(f"{finding.source}: {finding.rule}: {finding.snippet}")
        return 1
    print("SECRET_SCAN=OK")
    print(f"HISTORY_SCAN={'ON' if args.history else 'OFF'}")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
