import logging
from datetime import datetime, timedelta
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EVENT_HOMEASSISTANT_STARTED
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers import config_validation as cv
import voluptuous as vol

from .const import (
    DOMAIN,
    STORAGE_KEY,
    STORAGE_VERSION,
    FIELD_NAME,
    FIELD_RFID,
    FIELD_INTERVAL,
    FIELD_START_TIME,
    FIELD_END_TIME,
    FIELD_MEDIA_PLAYERS,
    FIELD_PHONES,
    FIELD_MESSAGE,
    FIELD_ACTIVE,
    FIELD_LAST_TRIGGERED,
    DEFAULT_INTERVAL,
    DEFAULT_START,
    DEFAULT_END,
    EVENT_REMINDER_TRIGGERED,
    EVENT_REMINDER_CLEARED,
    EVENT_RFID_SCANNED,
    SERVICE_ADD_REMINDER,
    SERVICE_REMOVE_REMINDER,
    SERVICE_CLEAR_REMINDER,
    PLATFORMS,
)

_LOGGER = logging.getLogger(__name__)

ADD_REMINDER_SCHEMA = vol.Schema({
    vol.Required(FIELD_NAME): cv.string,
    vol.Required(FIELD_RFID): cv.string,
    vol.Optional(FIELD_INTERVAL, default=DEFAULT_INTERVAL): vol.Coerce(float),
    vol.Optional(FIELD_START_TIME, default=DEFAULT_START): cv.time,
    vol.Optional(FIELD_END_TIME, default=DEFAULT_END): cv.time,
    vol.Optional(FIELD_MEDIA_PLAYERS, default=[]): vol.All(cv.ensure_list, [cv.entity_id]),
    vol.Optional(FIELD_PHONES, default=[]): vol.All(cv.ensure_list, [cv.string]),
    vol.Required(FIELD_MESSAGE): cv.string,
})

REMOVE_REMINDER_SCHEMA = vol.Schema({
    vol.Required(FIELD_NAME): cv.string,
})

CLEAR_REMINDER_SCHEMA = vol.Schema({
    vol.Required(FIELD_RFID): cv.string,
})

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        "store": store,
        "reminders": [],
        "known_tags": set(),
        "unsub_timer": None,
    }

    # Load stored reminders
    stored = await store.async_load()
    if stored:
        hass.data[DOMAIN][entry.entry_id]["reminders"] = stored.get("reminders", [])

    # Start monitoring loop
    async def monitor(now):
        await _check_reminders(hass, entry)

    async def start_monitoring(_):
        unsub = async_track_time_interval(hass, monitor, timedelta(seconds=60))
        hass.data[DOMAIN][entry.entry_id]["unsub_timer"] = unsub

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_monitoring)

    # Listen for RFID scans
    @callback
    async def handle_tag_scanned(event):
        tag = event.data.get("tag_id")
        if tag:
            hass.data[DOMAIN][entry.entry_id]["known_tags"].add(tag)
            await _process_scan(hass, entry, tag)

    hass.bus.async_listen("tag_scanned", handle_tag_scanned)

    # Register services
    async def add_reminder(call):
        data = call.data
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
        if any(r[FIELD_NAME] == data[FIELD_NAME] for r in reminders):
            _LOGGER.warning("Reminder %s already exists", data[FIELD_NAME])
            return
        new = {
            FIELD_NAME: data[FIELD_NAME],
            FIELD_RFID: data[FIELD_RFID],
            FIELD_INTERVAL: data[FIELD_INTERVAL],
            FIELD_START_TIME: str(data[FIELD_START_TIME]),
            FIELD_END_TIME: str(data[FIELD_END_TIME]),
            FIELD_MEDIA_PLAYERS: data[FIELD_MEDIA_PLAYERS],
            FIELD_PHONES: data[FIELD_PHONES],
            FIELD_MESSAGE: data[FIELD_MESSAGE],
            FIELD_ACTIVE: False,
            FIELD_LAST_TRIGGERED: None,
        }
        reminders.append(new)
        hass.data[DOMAIN][entry.entry_id]["known_tags"].add(data[FIELD_RFID])
        await _save(hass, entry)
        _LOGGER.info("Added reminder %s", data[FIELD_NAME])

    async def remove_reminder(call):
        name = call.data[FIELD_NAME]
        reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
        new = [r for r in reminders if r[FIELD_NAME] != name]
        if len(new) < len(reminders):
            hass.data[DOMAIN][entry.entry_id]["reminders"] = new
            await _save(hass, entry)
            _LOGGER.info("Removed reminder %s", name)

    async def clear_reminder(call):
        tag = call.data[FIELD_RFID]
        await _process_scan(hass, entry, tag)

    hass.services.async_register(DOMAIN, SERVICE_ADD_REMINDER, add_reminder, ADD_REMINDER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_REMOVE_REMINDER, remove_reminder, REMOVE_REMINDER_SCHEMA)
    hass.services.async_register(DOMAIN, SERVICE_CLEAR_REMINDER, clear_reminder, CLEAR_REMINDER_SCHEMA)

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    if unsub := hass.data[DOMAIN][entry.entry_id].get("unsub_timer"):
        unsub()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def _save(hass, entry):
    store = hass.data[DOMAIN][entry.entry_id]["store"]
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    await store.async_save({"reminders": reminders})

async def _check_reminders(hass, entry):
    now = datetime.now()
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    triggered = []

    for r in reminders:
        # Check if reminder is within time window
        start = datetime.strptime(r[FIELD_START_TIME], "%H:%M").time()
        end = datetime.strptime(r[FIELD_END_TIME], "%H:%M").time()
        if start <= end:
            in_window = start <= now.time() <= end
        else:
            in_window = now.time() >= start or now.time() <= end

        if not in_window:
            # If not in window, ensure it's inactive
            if r[FIELD_ACTIVE]:
                r[FIELD_ACTIVE] = False
            continue

        # Determine if it should be active now
        should_be_active = False
        last = r[FIELD_LAST_TRIGGERED]
        if last is None:
            should_be_active = True
        else:
            elapsed = now.timestamp() - last
            if elapsed >= r[FIELD_INTERVAL] * 3600:
                should_be_active = True

        if should_be_active and not r[FIELD_ACTIVE]:
            # Activate and fire event
            r[FIELD_ACTIVE] = True
            r[FIELD_LAST_TRIGGERED] = now.timestamp()
            triggered.append(r)
            hass.bus.async_fire(EVENT_REMINDER_TRIGGERED, r)
            _LOGGER.info("Triggered reminder %s", r[FIELD_NAME])
        elif not should_be_active and r[FIELD_ACTIVE]:
            # Deactivate if interval not yet elapsed (should not happen, but just in case)
            r[FIELD_ACTIVE] = False

    if triggered:
        await _save(hass, entry)

async def _process_scan(hass, entry, tag):
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    cleared = []
    for r in reminders:
        if r[FIELD_RFID] == tag and r[FIELD_ACTIVE]:
            r[FIELD_ACTIVE] = False
            cleared.append(r[FIELD_NAME])
    if cleared:
        await _save(hass, entry)
        hass.bus.async_fire(EVENT_REMINDER_CLEARED, {"tag": tag, "cleared": cleared})
        hass.bus.async_fire(EVENT_RFID_SCANNED, {"tag": tag, "cleared": cleared})
        _LOGGER.info("Cleared reminders %s with tag %s", cleared, tag)
