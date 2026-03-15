"""Sensor platform for RFID Medication Reminder."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ATTR_REMINDERS, ATTR_ACTIVE_REMINDERS, ATTR_TOTAL_REMINDERS

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([RFIDReminderSensor(coordinator, entry)], True)

class RFIDReminderSensor(CoordinatorEntity, SensorEntity):
    """Representation of a RFID Reminder sensor."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_sensor"
        self._attr_name = "RFID Medication Reminder Status"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        reminders = self._coordinator["reminders"]
        active = sum(1 for r in reminders if r.get("active", False))
        return active

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        reminders = self._coordinator["reminders"]
        return {
            ATTR_REMINDERS: reminders,
            ATTR_ACTIVE_REMINDERS: sum(1 for r in reminders if r.get("active", False)),
            ATTR_TOTAL_REMINDERS: len(reminders),
        }
