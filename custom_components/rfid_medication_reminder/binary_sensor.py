"""Binary sensor platform for RFID Medication Reminder condition monitoring."""
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from datetime import datetime

from .const import (
    DOMAIN,
    CONF_REMINDER_NAME,
    CONF_CONDITIONS,
    CONF_CONDITION_TYPE,
    ICON_CONDITION,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up binary sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = []

    # Create a condition status sensor for each reminder
    reminders = coordinator["reminders"]
    for i, reminder in enumerate(reminders):
        if reminder.get(CONF_CONDITIONS):
            sensors.append(ReminderConditionSensor(coordinator, entry, i, reminder))

    async_add_entities(sensors, True)

class ReminderConditionSensor(CoordinatorEntity, BinarySensorEntity):
    """Binary sensor indicating whether reminder conditions are currently met."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_conditions_{index}"
        self._attr_name = f"{reminder.get(CONF_REMINDER_NAME)} Conditions Met"
        self._attr_icon = ICON_CONDITION
        self._attr_device_class = "running"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )
        self._update_condition_state()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_condition_state()
        self.async_write_ha_state()

    def _update_condition_state(self):
        """Update the condition state."""
        from . import _check_conditions
        import asyncio

        # Run condition check
        try:
            loop = asyncio.get_running_loop()
            future = asyncio.run_coroutine_threadsafe(
                _check_conditions(self.hass, self._reminder, datetime.now()),
                loop
            )
            conditions_met = future.result(timeout=5)
            self._attr_is_on = conditions_met
        except Exception as err:
            self._attr_is_on = False
            self._attr_available = False

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        return {
            "reminder_name": self._reminder.get(CONF_REMINDER_NAME),
            "condition_type": self._reminder.get(CONF_CONDITION_TYPE, "all"),
            "has_conditions": bool(self._reminder.get(CONF_CONDITIONS)),
            "condition_count": len(self._reminder.get(CONF_CONDITIONS, [])),
        }
