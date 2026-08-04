#!/usr/bin/env bash
# Builds the PyInstaller bundle and packages it as a .deb.
#
# Usage:
#   packaging/build_deb.sh [version]
#
# Output: dist/noteapp_<version>_<arch>.deb
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VERSION="${1:-1.0.0}"
ARCH="$(dpkg --print-architecture)"
PKG_NAME="noteapp"
STAGE_DIR="$PROJECT_ROOT/build/deb/${PKG_NAME}_${VERSION}_${ARCH}"

cd "$PROJECT_ROOT"

echo "==> Building PyInstaller bundle"
rm -rf build/noteapp dist/NoteApp
pyinstaller packaging/noteapp.spec

echo "==> Staging .deb tree at $STAGE_DIR"
rm -rf "$STAGE_DIR"
mkdir -p "$STAGE_DIR/DEBIAN"
mkdir -p "$STAGE_DIR/opt/noteapp"
mkdir -p "$STAGE_DIR/usr/bin"
mkdir -p "$STAGE_DIR/usr/share/applications"

cp -r dist/NoteApp/. "$STAGE_DIR/opt/noteapp/"
ln -s /opt/noteapp/NoteApp "$STAGE_DIR/usr/bin/noteapp"

sed -e "s/\${VERSION}/${VERSION}/" -e "s/\${ARCH}/${ARCH}/" \
    "$PROJECT_ROOT/packaging/deb/control.template" > "$STAGE_DIR/DEBIAN/control"

cp "$PROJECT_ROOT/packaging/deb/noteapp.desktop" "$STAGE_DIR/usr/share/applications/noteapp.desktop"

echo "==> Staging icons into hicolor theme"
for size in 16 24 32 48 64 128 256 512; do
    icon_dir="$STAGE_DIR/usr/share/icons/hicolor/${size}x${size}/apps"
    mkdir -p "$icon_dir"
    cp "$PROJECT_ROOT/resources/icons/icon_${size}.png" "$icon_dir/noteapp.png"
done

cp "$PROJECT_ROOT/packaging/deb/postinst" "$STAGE_DIR/DEBIAN/postinst"
cp "$PROJECT_ROOT/packaging/deb/postrm" "$STAGE_DIR/DEBIAN/postrm"
chmod 755 "$STAGE_DIR/DEBIAN/postinst" "$STAGE_DIR/DEBIAN/postrm"

echo "==> Building .deb"
mkdir -p "$PROJECT_ROOT/dist"
dpkg-deb --root-owner-group --build "$STAGE_DIR" "$PROJECT_ROOT/dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"

echo "==> Done: dist/${PKG_NAME}_${VERSION}_${ARCH}.deb"
