"""Constants for the RFID Medication Reminder integration."""
from homeassistant.const import Platform

DOMAIN = "rfid_medication_reminder"
VERSION = "2.0.0"

PLATFORMS = [
    Platform.SENSOR,
    Platform.BUTTON,
    Platform.SELECT,
    Platform.NUMBER,
    Platform.TEXT,
    Platform.BINARY_SENSOR,
]

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

# Condition configuration keys
CONF_CONDITIONS = "conditions"
CONF_CONDITION_TYPE = "condition_type"
CONF_TIME_WINDOW = "time_window"
CONF_TIME_START = "time_start"
CONF_TIME_END = "time_end"
CONF_ENTITY_CONDITIONS = "entity_conditions"
CONF_CONDITION_ENTITY = "condition_entity"
CONF_CONDITION_STATE = "condition_state"
CONF_CONDITION_OPERATOR = "condition_operator"
CONF_CONDITION_VALUE = "condition_value"
CONF_WEEKDAYS = "weekdays"
CONF_DAYS_OF_MONTH = "days_of_month"
CONF_MONTHS = "months"

# Condition operators
OPERATOR_EQ = "eq"
OPERATOR_GT = "gt"
OPERATOR_LT = "lt"
OPERATOR_GTE = "gte"
OPERATOR_LTE = "lte"
OPERATOR_NE = "ne"
OPERATOR_IN = "in"
OPERATOR_NOT_IN = "not_in"
OPERATOR_HOME = "home"
OPERATOR_NOT_HOME = "not_home"

OPERATORS = [
    OPERATOR_EQ,
    OPERATOR_GT,
    OPERATOR_LT,
    OPERATOR_GTE,
    OPERATOR_LTE,
    OPERATOR_NE,
    OPERATOR_IN,
    OPERATOR_NOT_IN,
    OPERATOR_HOME,
    OPERATOR_NOT_HOME,
]

# Condition types
CONDITION_TYPE_ALL = "all"
CONDITION_TYPE_ANY = "any"
CONDITION_TYPE_NONE = "none"

CONDITION_TYPES = [
    CONDITION_TYPE_ALL,
    CONDITION_TYPE_ANY,
    CONDITION_TYPE_NONE,
]

# Weekdays
WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]

# Default values
DEFAULT_VOLUME = 0.7
DEFAULT_ENABLED = True
DEFAULT_ACTIVE = False
DEFAULT_CONDITION_TYPE = CONDITION_TYPE_ALL

# Storage
STORAGE_KEY = f"{DOMAIN}.storage"
STORAGE_VERSION = 2

# Events
EVENT_REMINDER_TRIGGERED = f"{DOMAIN}_triggered"
EVENT_REMINDER_CLEARED = f"{DOMAIN}_cleared"
EVENT_RFID_SCANNED = f"{DOMAIN}_rfid_scanned"
EVENT_CONDITION_MET = f"{DOMAIN}_condition_met"
EVENT_CONDITION_NOT_MET = f"{DOMAIN}_condition_not_met"

# Services
SERVICE_ADD_REMINDER = "add_reminder"
SERVICE_REMOVE_REMINDER = "remove_reminder"
SERVICE_UPDATE_REMINDER = "update_reminder"
SERVICE_CLEAR_REMINDER = "clear_reminder"
SERVICE_ADD_CONDITION = "add_condition"
SERVICE_REMOVE_CONDITION = "remove_condition"

# Attributes
ATTR_REMINDERS = "reminders"
ATTR_ACTIVE_REMINDERS = "active_reminders"
ATTR_TOTAL_REMINDERS = "total_reminders"
ATTR_CONDITIONS = "conditions"
ATTR_CONDITION_STATE = "condition_state"

# Icons
ICON_REMINDER = "mdi:bell-ring"
ICON_ACTIVE = "mdi:bell-ring-outline"
ICON_RFID = "mdi:rfid"
ICON_VOLUME = "mdi:volume-high"
ICON_INTERVAL = "mdi:timer"
ICON_MESSAGE = "mdi:message-text"
ICON_CONDITION = "mdi:script-text"
ICON_TIME = "mdi:clock"
ICON_CALENDAR = "mdi:calendar"
