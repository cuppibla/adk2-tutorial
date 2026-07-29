#!/bin/bash

# --- Function for error handling ---
handle_error() {
  echo -e "\n\n*******************************************************"
  echo "Error: $1"
  echo "*******************************************************"
  # Instead of exiting, we warn the user and wait for input
  echo "The script encountered an error."
  echo "Press [Enter] to ignore this error and attempt to continue."
  echo "Press [Ctrl+C] to exit the script completely."
  read -r
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "\n--- Running Project Creation and Billing Setup ---"

if [ -f "$SCRIPT_DIR/billing_enablement.py" ]; then
    python3 "$SCRIPT_DIR/billing_enablement.py" || handle_error "The billing enablement script failed."
elif [ -f "$SCRIPT_DIR/../scripts/billing_enablement.py" ]; then
    python3 "$SCRIPT_DIR/../scripts/billing_enablement.py" || handle_error "The billing enablement script failed."
else
    handle_error "billing_enablement.py script not found."
fi

echo -e "\n--- Billing Setup Complete ---"
