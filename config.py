"""
Application configuration constants.
Sensitive values (connection strings) are entered at runtime only — never stored here.
"""

# Microsoft Entra ID / MSAL settings
# Register your app at https://portal.azure.com → App registrations
# Set Redirect URI to: http://localhost  (Mobile and Desktop application)
AZURE_CLIENT_ID = "04b07795-8ddb-461a-bbee-02f9e1bf7b46"  # Azure CLI public client (demo)
AZURE_TENANT_ID = "common"  # 'common' allows any org/personal account
AZURE_AUTHORITY = f"https://login.microsoftonline.com/{AZURE_TENANT_ID}"

# Scopes for Fabric / Power BI access
FABRIC_SCOPES = [
    "https://analysis.windows.net/powerbi/api/.default",
]

# App metadata
APP_NAME = "Fabric Real-Time Data Generator"
APP_VERSION = "1.0.0"

# Streaming defaults
DEFAULT_EVENTS_PER_SECOND = 10
MIN_EVENTS_PER_SECOND = 10
MAX_EVENTS_PER_SECOND = 1000
EPS_OPTIONS = [10, 100, 500, 1000]  # discrete choices shown in the UI

# UI constants
LOG_MAX_LINES = 5000
STATS_UPDATE_INTERVAL_MS = 1000  # how often the EPS / total counter refreshes
