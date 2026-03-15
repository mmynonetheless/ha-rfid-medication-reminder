"""Button platform for RFID Medication Reminder."""
from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, ICON_REMINDER

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    buttons = []

    # Add New Reminder button
    buttons.append(AddReminderButton(coordinator, entry))

    async_add_entities(buttons, True)

class AddReminderButton(ButtonEntity):
    """Button to add a new reminder."""

    def __init__(self, coordinator, entry):
        """Initialize the button."""
        self._coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_add_reminder"
        self._attr_name = "Add New Reminder"
        self._attr_icon = ICON_REMINDER
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="RFID Medication Reminder",
            manufacturer="Community",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        self.hass.bus.async_fire(f"{DOMAIN}_show_add_form", {})
