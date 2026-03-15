"""Sensor platform for RFID Medication Reminder."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_REMINDERS,
    ATTR_ACTIVE_REMINDERS,
    ATTR_TOTAL_REMINDERS,
    ATTR_CONDITIONS,
    ICON_REMINDER,
    ICON_ACTIVE,
)

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor platform."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    sensors = [
        RFIDReminderStatusSensor(coordinator, entry),
        RFIDReminderListSensor(coordinator, entry),
        RFIDTagListSensor(coordinator, entry),
    ]

    # Create a sensor for each reminder
    reminders = coordinator["reminders"]
    for i, reminder in enumerate(reminders):
        sensors.append(IndividualReminderSensor(coordinator, entry, i, reminder))

    async_add_entities(sensors, True)

class RFIDReminderStatusSensor(CoordinatorEntity, SensorEntity):
    """Representation of the main status sensor."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_status"
        self._attr_name = "RFID Reminder Status"
        self._attr_icon = ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        """Return the state of the sensor."""
        reminders = self._coordinator["reminders"]
        return sum(1 for r in reminders if r.get("active", False))

    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        reminders = self._coordinator["reminders"]
        return {
            ATTR_ACTIVE_REMINDERS: sum(1 for r in reminders if r.get("active", False)),
            ATTR_TOTAL_REMINDERS: len(reminders),
            "reminder_names": [r.get("reminder_name", "") for r in reminders],
        }

class RFIDReminderListSensor(CoordinatorEntity, SensorEntity):
    """Sensor that lists all reminders with their conditions."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_list"
        self._attr_name = "RFID Reminder List"
        self._attr_icon = "mdi:format-list-bulleted"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        """Return the state."""
        return len(self._coordinator["reminders"])

    @property
    def extra_state_attributes(self):
        """Return detailed list of reminders with their conditions."""
        reminders = self._coordinator["reminders"]
        reminder_list = []
        for r in reminders:
            reminder_copy = r.copy()
            # Format conditions for display
            conditions = reminder_copy.get("conditions", [])
            if conditions:
                reminder_copy["has_conditions"] = True
                reminder_copy["condition_count"] = len(conditions)
            reminder_list.append(reminder_copy)
            
        return {
            ATTR_REMINDERS: reminder_list,
        }

class RFIDTagListSensor(CoordinatorEntity, SensorEntity):
    """Sensor that lists all known RFID tags."""

    def __init__(self, coordinator, entry):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_tag_list"
        self._attr_name = "RFID Tag List"
        self._attr_icon = "mdi:rfid"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        """Return number of known tags."""
        return len(self._coordinator.get("known_tags", set()))

    @property
    def extra_state_attributes(self):
        """Return list of known tags."""
        tags = list(self._coordinator.get("known_tags", set()))
        return {
            "tags": tags,
            "tag_count": len(tags),
        }

class IndividualReminderSensor(CoordinatorEntity, SensorEntity):
    """Sensor for an individual reminder with condition status."""

    def __init__(self, coordinator, entry, index, reminder):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._entry = entry
        self._index = index
        self._reminder = reminder
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_reminder_{index}"
        self._attr_name = f"{reminder.get('reminder_name', 'Unknown')}"
        self._attr_icon = ICON_ACTIVE if reminder.get("active") else ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    @property
    def native_value(self):
        """Return the state (active/inactive)."""
        return "active" if self._reminder.get("active") else "inactive"

    @property
    def extra_state_attributes(self):
        """Return reminder details including conditions."""
        reminder_copy = self._reminder.copy()
        conditions = reminder_copy.get("conditions", [])
        
        # Add condition summary
        if conditions:
            reminder_copy["condition_count"] = len(conditions)
            reminder_copy["condition_type"] = reminder_copy.get("condition_type", "all")
            
            # Add human-readable condition summary
            condition_summaries = []
            for condition in conditions:
                summary = []
                if condition.get("time_window"):
                    summary.append(f"Time: {condition.get('time_start', '00:00')}-{condition.get('time_end', '23:59')}")
                if condition.get("weekdays"):
                    summary.append(f"Days: {', '.join(condition['weekdays'])}")
                if condition.get("entity_conditions"):
                    for ec in condition["entity_conditions"]:
                        summary.append(f"Entity: {ec.get('condition_entity')} {ec.get('condition_operator')} {ec.get('condition_state', ec.get('condition_value'))}")
                condition_summaries.append(" | ".join(summary))
            reminder_copy["condition_summaries"] = condition_summaries
            
        return reminder_copy
