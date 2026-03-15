"""Constants for the RFID Medication Reminder integration."""

DOMAIN = "rfid_medication_reminder"
VERSION = "1.0.0"

# Configuration keys
CONF_REMINDER_NAME = "reminder_name"
CONF_RFID_TAG = "rfid_tag"
CONF_INTERVAL_HOURS = "interval_hours"
CONF_VOLUME = "volume"
CONF_MEDIA_PLAYERS = "media_players"
CONF_NOTIFICATION_TARGETS = "notification_targets"
CONF_CUSTOM_MESSAGE = "custom_message"
CONF_ENABLED = "enabled"
CONF_ACTIVE = "active"
CONF_LAST_TRIGGERED = "last_triggered"
CONF_SNOOZE_UNTIL = "snooze_until"

# Default values
DEFAULT_VOLUME = 0.7
DEFAULT_ENABLED = True
DEFAULT_ACTIVE = False

# Storage
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 1

# Events
EVENT_REMINDER_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_REMINDER_CLEARED = f"{DOMAIN}_cleared"
EVENT_REMINDER_SNOOZED = f"{DOMAIN}_snoozed"
EVENT_RFID_SCANNED = f"{DOMAIN}_rfid_scanned"

# Services
SERVICE_ADD_REMINDER = "add_reminder"
SERVICE_REMOVE_REMINDER = "remove_reminder"
SERVICE_UPDATE_REMINDER = "update_reminder"
SERVICE_CLEAR_REMINDER = "clear_reminder"
SERVICE_SNOOZE_REMINDER = "snooze_reminder"

# Attributes
ATTR_REMINDERS = "reminders"
ATTR_ACTIVE_REMINDERS = "active_reminders"
ATTR_TOTAL_REMINDERS = "total_reminders"
