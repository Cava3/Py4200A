#!/bin/bash

# Ensure the script is run with root privileges
if [ "$EUID" -ne 0 ]; then
  echo "Error: Please run this script with sudo."
  exit 1
fi

# Determine the actual user (since sudo changes $USER to root)
TARGET_USER=${SUDO_USER:-$USER}

echo "--- Setting up GPIB Permissions and Udev Rules ---"

# 1. Safely check for and create the 'gpib' group
if getent group gpib > /dev/null 2>&1; then
    echo "[INFO] Group 'gpib' already exists. Skipping creation."
else
    echo "[ACTION] Creating 'gpib' group..."
    groupadd gpib
fi

# 2. Add the target user to the group
echo "[ACTION] Adding user '$TARGET_USER' to the 'gpib' group..."
usermod -aG gpib "$TARGET_USER"

# 3. Create the udev rules
echo "[ACTION] Writing udev rules to /etc/udev/rules.d/..."

# Permissions rule
cat << 'EOF' > /etc/udev/rules.d/98-gpib-perms.rules
# Automatically assign /dev/gpib* to the gpib group with read/write access
KERNEL=="gpib[0-9]*", MODE="0660", GROUP="gpib"
EOF

# Auto-initialization rule
cat << 'EOF' > /etc/udev/rules.d/99-gpib-init.rules
# Automatically run gpib_config when National Instruments (3923) USB is plugged in
SUBSYSTEM=="usb", ACTION=="add", ATTRS{idVendor}=="3923", RUN+="/usr/local/sbin/gpib_config"
EOF

# 4. Apply the changes
echo "[ACTION] Reloading udev rules..."
udevadm control --reload-rules
udevadm trigger

echo "------------------------------------------------------"
echo "Setup Complete!"
echo "IMPORTANT: You must RESTART your computer (or log out and log back in) for the group permission changes to apply to your user account."