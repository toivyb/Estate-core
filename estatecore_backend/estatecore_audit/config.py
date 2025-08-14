import os

# Base directory on the server for client files
ESTATECORE_DATA_DIR = os.environ.get("ESTATECORE_DATA_DIR", "/data/clients")

# Path names used inside each client folder
CLIENT_SUBFOLDERS = {
    "buildings": "buildings",
    "tenants": "tenants",
    "audit": "audit",
}

# Audit log filename per client
AUDIT_LOG_NAME = "log.txt"
