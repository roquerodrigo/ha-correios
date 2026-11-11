"""Sensor que expõe o status mais recente de um único pacote."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity

from ..package_entity import CorreiosPackageEntity

if TYPE_CHECKING:
    from ..data import CorreiosPackageEvent

type PackageAttribute = str | bool | list[dict[str, str | None]] | None

MAX_STATE_LENGTH = 255


def _event_attributes(event: CorreiosPackageEvent) -> dict[str, str | None]:
    return {
        "description": event.description,
        "detail": event.detail or None,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "unit": event.unit or None,
        "location": event.location or None,
        "destination_unit": event.destination_unit or None,
        "destination": event.destination or None,
    }


class CorreiosPackageSensor(CorreiosPackageEntity, SensorEntity):
    """Status de rastreamento mais recente de um pacote, no subdispositivo dele."""

    _attr_name = None
    _attr_translation_key = "package"
    _unrecorded_attributes = frozenset({"events"})

    @property
    def native_value(self) -> str | None:
        """Retorna o status mais recente informado para o pacote."""
        package = self.package
        return package.status[:MAX_STATE_LENGTH] if package is not None else None

    @property
    def extra_state_attributes(self) -> dict[str, PackageAttribute]:
        """Expõe os detalhes e o histórico de eventos do pacote."""
        package = self.package
        if package is None:
            return {}
        return {
            "tracking_code": package.tracking_code,
            "direction": package.direction.value,
            "delivered": package.delivered,
            "delayed": package.delayed,
            "detail": package.status_detail or None,
            "unit": package.unit or None,
            "location": package.location or None,
            "destination_unit": package.destination_unit or None,
            "destination": package.destination or None,
            "category": package.category or None,
            "expected_delivery": package.expected_delivery.isoformat()
            if package.expected_delivery
            else None,
            "last_event_at": package.last_event_at.isoformat()
            if package.last_event_at
            else None,
            "events": [_event_attributes(event) for event in package.events],
        }
