"""Init for RFID Medication Reminder integration."""
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType
import voluptuous as vol

from .const import (
    DOMAIN,
    CONF_REMINDER_NAME,
    CONF_RFID_TAG,
    CONF_INTERVAL_HOURS,
    CONF_VOLUME,
    CONF_MEDIA_PLAYERS,
    CONF_NOTIFICATION_TARGETS,
    CONF_CUSTOM_MESSAGE,
    CONF_ENABLED,
    CONF_ACTIVE,
    CONF_LAST_TRIGGERED,
    CONF_SNOOZE_UNTIL,
    DEFAULT_VOLUME,
    DEFAULT_ENABLED,
    DEFAULT_ACTIVE,
    STORAGE_KEY,
    STORAGE_VERSION,
    EVENT_REMINDER_TRIGGERED,
    EVENT_REMINDER_CLEARED,
    EVENT_REMINDER_SNOOZED,
    EVENT_RFID_SCANNED,
    SERVICE_ADD_REMINDER,
    SERVICE_REMOVE_REMINDER,
    SERVICE_UPDATE_REMINDER,
    SERVICE_CLEAR_REMINDER,
    SERVICE_SNOOZE_REMINDER,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor"]

# Service schemas
ADD_REMINDER_SCHEMA = vol.Schema({
    vol.Required(CONF_REMINDER_NAME): cv.string,
    vol.Required(CONF_RFID_TAG): cv.string,
    vol.Required(CONF_INTERVAL_HOURS): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=24)),
    vol.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
    vol.Optional(CONF_MEDIA_PLAYERS, default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_NOTIFICATION_TARGETS, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Required(CONF_CUSTOM_MESSAGE): cv.string,
})

REMOVE_REMINDER_SCHEMA = vol.Schema({
    vol.Required(CONF_REMINDER_NAME): cv.string,
})

UPDATE_REMINDER_SCHEMA = vol.Schema({
    vol.Required(CONF_REMINDER_NAME): cv.string,
    vol.Optional(CONF_RFID_TAG): cv.string,
    vol.Optional(CONF_INTERVAL_HOURS): vol.All(vol.Coerce(float), vol.Range(min=0.5, max=24)),
    vol.Optional(CONF_VOLUME): vol.All(vol.Coerce(float), vol.Range(min=0.1, max=1.0)),
    vol.Optional(CONF_MEDIA_PLAYERS): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(CONF_NOTIFICATION_TARGETS): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_CUSTOM_MESSAGE): cv.string,
    vol.Optional(CONF_ENABLED): cv.boolean,
})

CLEAR_REMINDER_SCHEMA = vol.Schema({
    vol.Required(CONF_RFID_TAG): cv.string,
})

SNOOZE_REMINDER_SCHEMA = vol.Schema({
    vol.Required(CONF_REMINDER_NAME): cv.string,
    vol.Optional("minutes", default=10): vol.All(vol.Coerce(int), vol.Range(min=1, max=60)),
})

async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the RFID Medication Reminder component."""
    hass.data.setdefault(DOMAIN, {})
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Medication Reminder from a config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "reminders": [],
        "unsub_timer": None,
    }

    # Load stored reminders
    stored = await store.async_load()
    if stored:
        hass.data[DOMAIN][entry.entry_id]["reminders"] = stored.get("reminders", [])

    # Register services
    await _register_services(hass, entry)

    # Start monitoring
    async def start_monitoring(_):
        """Start the monitoring interval."""
        unsub = async_track_time_interval(
            hass,
            lambda now: _check_reminders(hass, entry),
            timedelta(seconds=60)
        )
        hass.data[DOMAIN][entry.entry_id]["unsub_timer"] = unsub

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_monitoring)

    # Listen for RFID tag scans
    @callback
    async def handle_tag_scanned(event):
        """Handle RFID tag scanned event."""
        tag_id = event.data.get("tag_id")
        if tag_id:
            await _process_rfid_scan(hass, entry, tag_id)

    hass.bus.async_listen("tag_scanned", handle_tag_scanned)

    # Forward setup to sensor platform
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unsub := hass.data[DOMAIN][entry.entry_id].get("unsub_timer"):
        unsub()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def _register_services(hass: HomeAssistant, entry: ConfigEntry):
    """Register services for this integration."""
    
    async def add_reminder(call: ServiceCall) -> None:
        """Add a new reminder."""
        data = call.data
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]

        # Check if reminder already exists
        if any(r[CONF_REMINDER_NAME] == data[CONF_REMINDER_NAME] for r in reminders):
            _LOGGER.warning("Reminder '%s' already exists", data[CONF_REMINDER_NAME])
            return

        new_reminder = {
            CONF_REMINDER_NAME: data[CONF_REMINDER_NAME],
            CONF_RFID_TAG: data[CONF_RFID_TAG],
            CONF_INTERVAL_HOURS: data[CONF_INTERVAL_HOURS],
            CONF_VOLUME: data.get(CONF_VOLUME, DEFAULT_VOLUME),
            CONF_MEDIA_PLAYERS: data.get(CONF_MEDIA_PLAYERS, []),
            CONF_NOTIFICATION_TARGETS: data.get(CONF_NOTIFICATION_TARGETS, []),
            CONF_CUSTOM_MESSAGE: data[CONF_CUSTOM_MESSAGE],
            CONF_ENABLED: DEFAULT_ENABLED,
            CONF_ACTIVE: DEFAULT_ACTIVE,
            CONF_LAST_TRIGGERED: None,
            CONF_SNOOZE_UNTIL: None,
        }

        reminders.append(new_reminder)
        await _save_reminders(hass, entry)
        _LOGGER.info("Added reminder '%s'", data[CONF_REMINDER_NAME])

    async def remove_reminder(call: ServiceCall) -> None:
        """Remove a reminder."""
        name = call.data[CONF_REMINDER_NAME]
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]

        new_reminders = [r for r in reminders if r[CONF_REMINDER_NAME] != name]

        if len(new_reminders) < len(reminders):
            hass.data[DOMAIN][entry.entry_id]["reminders"] = new_reminders
            await _save_reminders(hass, entry)
            _LOGGER.info("Removed reminder '%s'", name)

    async def update_reminder(call: ServiceCall) -> None:
        """Update an existing reminder."""
        data = call.data
        name = data[CONF_REMINDER_NAME]
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]

        for i, r in enumerate(reminders):
            if r[CONF_REMINDER_NAME] == name:
                updated = r.copy()
                if CONF_RFID_TAG in data:
                    updated[CONF_RFID_TAG] = data[CONF_RFID_TAG]
                if CONF_INTERVAL_HOURS in data:
                    updated[CONF_INTERVAL_HOURS] = data[CONF_INTERVAL_HOURS]
                if CONF_VOLUME in data:
                    updated[CONF_VOLUME] = data[CONF_VOLUME]
                if CONF_MEDIA_PLAYERS in data:
                    updated[CONF_MEDIA_PLAYERS] = data[CONF_MEDIA_PLAYERS]
                if CONF_NOTIFICATION_TARGETS in data:
                    updated[CONF_NOTIFICATION_TARGETS] = data[CONF_NOTIFICATION_TARGETS]
                if CONF_CUSTOM_MESSAGE in data:
                    updated[CONF_CUSTOM_MESSAGE] = data[CONF_CUSTOM_MESSAGE]
                if CONF_ENABLED in data:
                    updated[CONF_ENABLED] = data[CONF_ENABLED]

                reminders[i] = updated
                await _save_reminders(hass, entry)
                _LOGGER.info("Updated reminder '%s'", name)
                break

    async def clear_reminder(call: ServiceCall) -> None:
        """Clear reminder by RFID tag."""
        tag_id = call.data[CONF_RFID_TAG]
        await _process_rfid_scan(hass, entry, tag_id)

    async def snooze_reminder(call: ServiceCall) -> None:
        """Snooze a reminder."""
        name = call.data[CONF_REMINDER_NAME]
        minutes = call.data.get("minutes", 10)
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]

        snooze_until = (datetime.now() + timedelta(minutes=minutes)).timestamp()

        for i, r in enumerate(reminders):
            if r[CONF_REMINDER_NAME] == name and r[CONF_ACTIVE]:
                r[CONF_ACTIVE] = False
                r[CONF_SNOOZE_UNTIL] = snooze_until
                await _save_reminders(hass, entry)
                hass.bus.async_fire(EVENT_REMINDER_SNOOZED, {
                    CONF_REMINDER_NAME: name,
                    "snooze_minutes": minutes
                })
                _LOGGER.info("Snoozed reminder '%s' for %d minutes", name, minutes)
                break

    hass.services.async_register(
        DOMAIN, SERVICE_ADD_REMINDER, add_reminder, schema=ADD_REMINDER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_REMOVE_REMINDER, remove_reminder, schema=REMOVE_REMINDER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_UPDATE_REMINDER, update_reminder, schema=UPDATE_REMINDER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_CLEAR_REMINDER, clear_reminder, schema=CLEAR_REMINDER_SCHEMA
    )
    hass.services.async_register(
        DOMAIN, SERVICE_SNOOZE_REMINDER, snooze_reminder, schema=SNOOZE_REMINDER_SCHEMA
    )

async def _check_reminders(hass: HomeAssistant, entry: ConfigEntry):
    """Check all reminders and trigger if needed."""
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    now_ts = datetime.now().timestamp()
    triggered = []

    for r in reminders:
        if not r[CONF_ENABLED] or r[CONF_ACTIVE]:
            continue

        # Check snooze
        snooze_until = r.get(CONF_SNOOZE_UNTIL)
        if snooze_until and snooze_until > now_ts:
            continue

        # Check interval
        last = r.get(CONF_LAST_TRIGGERED)
        if last is None or (now_ts - last) > (r[CONF_INTERVAL_HOURS] * 3600):
            r[CONF_ACTIVE] = True
            r[CONF_LAST_TRIGGERED] = now_ts
            triggered.append(r[CONF_REMINDER_NAME])
            hass.bus.async_fire(EVENT_REMINDER_TRIGGERED, {
                CONF_REMINDER_NAME: r[CONF_REMINDER_NAME],
                CONF_RFID_TAG: r[CONF_RFID_TAG],
                CONF_CUSTOM_MESSAGE: r[CONF_CUSTOM_MESSAGE],
                CONF_VOLUME: r[CONF_VOLUME],
                CONF_MEDIA_PLAYERS: r[CONF_MEDIA_PLAYERS],
                CONF_NOTIFICATION_TARGETS: r[CONF_NOTIFICATION_TARGETS],
            })

    if triggered:
        await _save_reminders(hass, entry)
        _LOGGER.debug("Triggered reminders: %s", ", ".join(triggered))

async def _process_rfid_scan(hass: HomeAssistant, entry: ConfigEntry, tag_id: str):
    """Process an RFID tag scan."""
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    cleared = []

    for r in reminders:
        if r[CONF_RFID_TAG] == tag_id and r[CONF_ACTIVE]:
            r[CONF_ACTIVE] = False
            r[CONF_SNOOZE_UNTIL] = None
            cleared.append(r[CONF_REMINDER_NAME])

    if cleared:
        await _save_reminders(hass, entry)
        hass.bus.async_fire(EVENT_REMINDER_CLEARED, {
            CONF_RFID_TAG: tag_id,
            "cleared_reminders": cleared
        })
        hass.bus.async_fire(EVENT_RFID_SCANNED, {
            CONF_RFID_TAG: tag_id,
            "cleared_reminders": cleared
        })
        _LOGGER.info("RFID tag %s cleared reminders: %s", tag_id, ", ".join(cleared))

async def _save_reminders(hass: HomeAssistant, entry: ConfigEntry):
    """Save reminders to storage."""
    store = hass.data[DOMAIN][entry.entry_id]["store"]
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    await store.async_save({"reminders": reminders})
