#!/usr/bin/env bash
set -euo pipefail

EXPECTED_PACKAGES=(
    "py4200A/__init__.py"
    "py4200A/src/__init__.py"
    "py4200A/src/KI4200A.py"
    "py4200A/src/consts.py"
    "py4200A/src/boards/__init__.py"
    "py4200A/src/results/__init__.py"
    "py4200A/src/error/__init__.py"
    "py4200A/src/realtime/__init__.py"
)

# ── 1. Clean ──────────────────────────────────────────────────────────────────
echo "==> Cleaning previous build artifacts..."
rm -rf dist/ *.egg-info/

# ── 2. Build ──────────────────────────────────────────────────────────────────
echo "==> Building package..."
python -m build

WHEEL=$(ls dist/*.whl | head -n 1)
echo "==> Built wheel: $WHEEL"

# ── 3. Check subpackages ──────────────────────────────────────────────────────
echo ""
echo "==> Checking wheel contents..."
WHEEL_CONTENTS=$(unzip -l "$WHEEL")

ALL_OK=true
for entry in "${EXPECTED_PACKAGES[@]}"; do
    if echo "$WHEEL_CONTENTS" | grep -q "$entry"; then
        echo "  [OK] $entry"
    else
        echo "  [MISSING] $entry"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    echo ""
    echo "ERROR: Some expected files are missing from the wheel. Aborting."
    echo ""
    echo "Full wheel contents:"
    echo "$WHEEL_CONTENTS"
    exit 1
fi

# ── 4. Upload to TestPyPI ─────────────────────────────────────────────────────
echo ""
echo "==> Uploading to TestPyPI..."
twine upload --repository testpypi dist/*

echo ""
echo "Done. Install from TestPyPI with:"
echo "  pip install --index-url https://test.pypi.org/simple/ py4200A"
