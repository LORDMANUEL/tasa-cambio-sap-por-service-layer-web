#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${VERSION:-5.0.0}"
ARCH="${ARCH:-amd64}"
BUILD="$ROOT/dist/deb-root"
OUT="$ROOT/dist"

rm -rf "$BUILD"
mkdir -p "$BUILD/DEBIAN" "$BUILD/opt/atas" "$BUILD/lib/systemd/system" "$BUILD/usr/share/applications" "$BUILD/usr/bin"

cp "$ROOT/packaging/debian/control" "$BUILD/DEBIAN/control"
sed -i "s/^Version:.*/Version: $VERSION/" "$BUILD/DEBIAN/control"
cp "$ROOT/packaging/debian/postinst" "$ROOT/packaging/debian/prerm" "$ROOT/packaging/debian/postrm" "$BUILD/DEBIAN/"
chmod 0755 "$BUILD/DEBIAN/"{postinst,prerm,postrm}

rsync -a --exclude '.git' --exclude '.github' --exclude '.venv' --exclude '.env' --exclude 'dist' --exclude 'build' --exclude 'site' --exclude 'runtime' --exclude '__pycache__' --exclude '.pytest_cache' "$ROOT/" "$BUILD/opt/atas/"

cp "$ROOT/packaging/debian/atas.service" "$BUILD/lib/systemd/system/"
cp "$ROOT/packaging/debian/atas.desktop" "$BUILD/usr/share/applications/"
cp "$ROOT/packaging/debian/atas" "$BUILD/usr/bin/"
chmod 0755 "$BUILD/usr/bin/atas"

mkdir -p "$OUT"
dpkg-deb --root-owner-group --build "$BUILD" "$OUT/atas_${VERSION}_${ARCH}.deb"
