#!/usr/bin/env bash
set -euo pipefail

GREEN="\033[0;32m"
RED="\033[0;31m"
RESET="\033[0m"

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
T_START=$SECONDS
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
        echo -e "  ${GREEN}[OK]${RESET} $entry"
    else
        echo -e "  ${RED}[MISSING]${RESET} $entry"
        ALL_OK=false
    fi
done

if [ "$ALL_OK" = false ]; then
    echo ""
    echo -e "${RED}ERROR:${RESET} Some expected files are missing from the wheel. Aborting."
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
echo -e "${GREEN}[BUILD  AND TEST PUBLISH SUCCESSFUL in $((SECONDS - T_START)) seconds]${RESET}"
echo ""
echo "Done. Install from TestPyPI with:"
echo "  pip install --index-url https://test.pypi.org/simple/ py4200A"
