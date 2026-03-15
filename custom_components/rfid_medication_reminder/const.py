DOMAIN = "rfid_reminder"
VERSION = "2.0.0"

STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 2

# Reminder fields
FIELD_NAME = "name"
FIELD_RFID = "rfid_tag"
FIELD_INTERVAL = "interval_hours"
FIELD_START_TIME = "start_time"
FIELD_END_TIME = "end_time"
FIELD_MEDIA_PLAYERS = "media_players"
FIELD_PHONES = "phones"
FIELD_MESSAGE = "message"
FIELD_ACTIVE = "active"
FIELD_LAST_TRIGGERED = "last_triggered"

# Defaults
DEFAULT_INTERVAL = 4.0
DEFAULT_START = "00:00"
DEFAULT_END = "23:59"

# Events
EVENT_REMINDER_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_REMINDER_CLEARED = f"{DOMAIN}_cleared"
EVENT_RFID_SCANNED = f"{DOMAIN}_rfid_scanned"

# Services
SERVICE_ADD_REMINDER = "add_reminder"
SERVICE_REMOVE_REMINDER = "remove_reminder"
SERVICE_CLEAR_REMINDER = "clear_reminder"

PLATFORMS = ["sensor", "select", "button"]
