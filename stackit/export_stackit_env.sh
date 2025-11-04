#!/bin/bash
# ------------------------------------------------------------------
# Script to export STACKIT environment variables and fetch auth token
# ------------------------------------------------------------------

# === USER CONFIGURABLE VARIABLES ===
PROJECT_ID="your_project_id_here"
REGION="your_region_here"
NETWORK_ID="your_network_id_here"
SERVICE_ACCOUNT_KEY="sa-key-6e45f94f-8554-42a0-8475-5995b9bdbe51.json"

# === CHECK PREREQUISITES ===
if ! command -v stackit &> /dev/null; then
  echo "Error: stackit CLI is not installed or not in PATH."
  exit 1
fi

if [ ! -f "$SERVICE_ACCOUNT_KEY" ]; then
  echo "Error: Service account key file not found: $SERVICE_ACCOUNT_KEY"
  exit 1
fi

# === AUTHENTICATE SERVICE ACCOUNT ===
echo "Activating service account..."
echo "Note that token will be valid for 60 minutes..."
stackit auth activate-service-account --service-account-key-path "$SERVICE_ACCOUNT_KEY"
if [ $? -ne 0 ]; then
  echo "Error: Failed to activate service account."
  exit 1
fi

# === GET STACKIT TOKEN ===
echo "Fetching STACKIT access token..."
STACKIT_TOKEN=$(stackit auth activate-service-account \
  --service-account-key-path "$SERVICE_ACCOUNT_KEY" \
  --only-print-access-token)

if [ -z "$STACKIT_TOKEN" ]; then
  echo "Error: Failed to retrieve STACKIT token."
  exit 1
fi

# === EXPORT ENVIRONMENT VARIABLES ===
export PROJECT_ID
export REGION
export NETWORK_ID
export STACKIT_TOKEN

# === DISPLAY EXPORTED VARIABLES ===
echo ""
echo "✅ Environment variables exported successfully:"
echo "PROJECT_ID=${PROJECT_ID}"
echo "REGION=${REGION}"
echo "NETWORK_ID=${NETWORK_ID}"
echo "STACKIT_TOKEN=${STACKIT_TOKEN:0:20}********"  # Masked for safety

# === OPTIONAL ===
# Save exports for future shell sessions
# echo "export PROJECT_ID=$PROJECT_ID" >> ~/.bashrc
# echo "export REGION=$REGION" >> ~/.bashrc
# echo "export NETWORK_ID=$NETWORK_ID" >> ~/.bashrc

