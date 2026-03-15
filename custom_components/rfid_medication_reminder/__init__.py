"""Init for RFID Medication Reminder integration."""
import logging
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    STATE_HOME,
    STATE_ON,
)
from homeassistant.helpers.storage import Store
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_state_change_event,
)
from homeassistant.helpers import device_registry as dr

from .const import (
    DOMAIN,
    PLATFORMS,
    VERSION,
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
    CONF_CONDITIONS,
    CONF_CONDITION_TYPE,
    CONF_TIME_WINDOW,
    CONF_TIME_START,
    CONF_TIME_END,
    CONF_ENTITY_CONDITIONS,
    CONF_CONDITION_ENTITY,
    CONF_CONDITION_OPERATOR,
    CONF_CONDITION_STATE,
    CONF_CONDITION_VALUE,
    CONF_WEEKDAYS,
    DEFAULT_VOLUME,
    DEFAULT_ENABLED,
    DEFAULT_ACTIVE,
    DEFAULT_CONDITION_TYPE,
    STORAGE_KEY,
    STORAGE_VERSION,
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
    CONDITION_TYPE_ALL,
    CONDITION_TYPE_ANY,
    CONDITION_TYPE_NONE,
    EVENT_REMINDER_TRIGGERED,
    EVENT_REMINDER_CLEARED,
    EVENT_RFID_SCANNED,
    EVENT_CONDITION_MET,
    EVENT_CONDITION_NOT_MET,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up RFID Medication Reminder from a config entry."""
    store = Store(hass, STORAGE_VERSION, STORAGE_KEY)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "store": store,
        "reminders": [],
        "unsub_timer": None,
        "condition_listeners": {},
        "known_tags": set(),
    }

    # Create device registry entry
    device_registry = dr.async_get(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, entry.entry_id)},
        name="RFID Medication Reminder",
        manufacturer="Community",
        model="Conditional RFID Reminder",
        sw_version=VERSION,
    )

    # Load stored reminders
    stored = await store.async_load()
    if stored:
        hass.data[DOMAIN][entry.entry_id]["reminders"] = stored.get("reminders", [])

    # Start monitoring
    async def start_monitoring(_):
        unsub = async_track_time_interval(
            hass,
            lambda now: _check_reminders(hass, entry),
            timedelta(seconds=60)
        )
        hass.data[DOMAIN][entry.entry_id]["unsub_timer"] = unsub
        await _setup_condition_listeners(hass, entry)

    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, start_monitoring)

    # Listen for RFID tag scans
    @callback
    async def handle_tag_scanned(event):
        tag_id = event.data.get("tag_id")
        if tag_id:
            await _update_known_tags(hass, entry, tag_id)
            await _process_rfid_scan(hass, entry, tag_id)

    hass.bus.async_listen("tag_scanned", handle_tag_scanned)

    # Forward setup to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unsub := hass.data[DOMAIN][entry.entry_id].get("unsub_timer"):
        unsub()
    for unsub in hass.data[DOMAIN][entry.entry_id]["condition_listeners"].values():
        unsub()
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

def get_known_tags(hass: HomeAssistant, entry_id: str) -> set:
    """Return set of known RFID tags."""
    return hass.data[DOMAIN][entry_id].get("known_tags", set())

async def _update_known_tags(hass: HomeAssistant, entry: ConfigEntry, tag: str):
    """Add a tag to the known_tags set if not already present."""
    if tag:
        hass.data[DOMAIN][entry.entry_id]["known_tags"].add(tag)

async def _setup_condition_listeners(hass: HomeAssistant, entry: ConfigEntry):
    """Set up state change listeners for condition entities."""
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    entities_to_watch = set()
    for reminder in reminders:
        for condition in reminder.get(CONF_CONDITIONS, []):
            for ec in condition.get(CONF_ENTITY_CONDITIONS, []):
                if entity := ec.get(CONF_CONDITION_ENTITY):
                    entities_to_watch.add(entity)
    if not entities_to_watch:
        return

    @callback
    async def condition_state_changed(event):
        if event.data.get("entity_id") in entities_to_watch:
            await _check_reminders(hass, entry)

    unsub = async_track_state_change_event(
        hass, list(entities_to_watch), condition_state_changed
    )
    hass.data[DOMAIN][entry.entry_id]["condition_listeners"]["state"] = unsub

async def _check_reminders(hass: HomeAssistant, entry: ConfigEntry):
    """Check all reminders and trigger if needed."""
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    now = datetime.now()
    now_ts = now.timestamp()
    triggered = []

    for r in reminders:
        if not r.get(CONF_ENABLED, True) or r.get(CONF_ACTIVE, False):
            continue
        if not await _check_conditions(hass, r, now):
            continue
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
            hass.bus.async_fire(EVENT_CONDITION_MET, {
                CONF_REMINDER_NAME: r[CONF_REMINDER_NAME],
            })

    if triggered:
        await _save_reminders(hass, entry)
        _LOGGER.debug("Triggered reminders: %s", ", ".join(triggered))

async def _check_conditions(hass: HomeAssistant, reminder: dict, now: datetime) -> bool:
    """Check if all conditions for a reminder are met."""
    conditions = reminder.get(CONF_CONDITIONS, [])
    if not conditions:
        return True
    condition_type = reminder.get(CONF_CONDITION_TYPE, CONDITION_TYPE_ALL)
    results = []
    for condition in conditions:
        results.append(await _check_single_condition(hass, condition, now))
    if condition_type == CONDITION_TYPE_ALL:
        return all(results)
    if condition_type == CONDITION_TYPE_ANY:
        return any(results)
    if condition_type == CONDITION_TYPE_NONE:
        return not any(results)
    return True

async def _check_single_condition(hass: HomeAssistant, condition: dict, now: datetime) -> bool:
    """Check a single condition."""
    # Time window
    if condition.get(CONF_TIME_WINDOW):
        try:
            start = datetime.strptime(condition.get(CONF_TIME_START, "00:00"), "%H:%M").time()
            end = datetime.strptime(condition.get(CONF_TIME_END, "23:59"), "%H:%M").time()
            cur = now.time()
            if start <= end:
                if not (start <= cur <= end):
                    return False
            else:  # overnight
                if not (cur >= start or cur <= end):
                    return False
        except ValueError:
            return False

    # Weekday
    if weekdays := condition.get(CONF_WEEKDAYS):
        if now.strftime("%A").lower() not in weekdays:
            return False

    # Entity conditions
    for ec in condition.get(CONF_ENTITY_CONDITIONS, []):
        entity_id = ec.get(CONF_CONDITION_ENTITY)
        operator = ec.get(CONF_CONDITION_OPERATOR, OPERATOR_EQ)
        expected = ec.get(CONF_CONDITION_STATE) or ec.get(CONF_CONDITION_VALUE)
        if not entity_id:
            continue
        state = hass.states.get(entity_id)
        if not state:
            return False
        current = state.state

        if operator == OPERATOR_HOME:
            if current not in [STATE_HOME, STATE_ON]:
                return False
            continue
        if operator == OPERATOR_NOT_HOME:
            if current in [STATE_HOME, STATE_ON]:
                return False
            continue

        if operator == OPERATOR_EQ:
            if current != str(expected):
                return False
        elif operator == OPERATOR_NE:
            if current == str(expected):
                return False
        elif operator in [OPERATOR_GT, OPERATOR_LT, OPERATOR_GTE, OPERATOR_LTE]:
            try:
                cur_val = float(current)
                exp_val = float(expected)
                if operator == OPERATOR_GT and not (cur_val > exp_val):
                    return False
                if operator == OPERATOR_LT and not (cur_val < exp_val):
                    return False
                if operator == OPERATOR_GTE and not (cur_val >= exp_val):
                    return False
                if operator == OPERATOR_LTE and not (cur_val <= exp_val):
                    return False
            except ValueError:
                return False
        elif operator == OPERATOR_IN:
            exp_list = expected if isinstance(expected, list) else [expected]
            if current not in [str(e) for e in exp_list]:
                return False
        elif operator == OPERATOR_NOT_IN:
            exp_list = expected if isinstance(expected, list) else [expected]
            if current in [str(e) for e in exp_list]:
                return False
    return True

async def _process_rfid_scan(hass: HomeAssistant, entry: ConfigEntry, tag_id: str):
    """Clear reminders for a scanned tag."""
    reminders = hass.data[DOMAIN][entry.entry_id]["reminders"]
    cleared = []
    for r in reminders:
        if r.get(CONF_RFID_TAG) == tag_id and r.get(CONF_ACTIVE, False):
            r[CONF_ACTIVE] = False
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
