"""Sensor que expõe o status mais recente de um único pacote."""

from __future__ import annotations

from typing import TYPE_CHECKING

from homeassistant.components.sensor import SensorEntity

from ..entity import CorreiosEntity

if TYPE_CHECKING:
    from ..coordinator import CorreiosDataUpdateCoordinator
    from ..data import CorreiosPackage, CorreiosPackageEvent

type PackageAttribute = str | bool | list[dict[str, str | None]] | None

MAX_STATE_LENGTH = 255


def package_sensor_unique_id(entry_id: str, tracking_code: str) -> str:
    """Retorna o unique id do sensor que acompanha ``tracking_code``."""
    return f"{entry_id}_package_{tracking_code.lower()}"


def _event_attributes(event: CorreiosPackageEvent) -> dict[str, str | None]:
    return {
        "description": event.description,
        "detail": event.detail or None,
        "occurred_at": event.occurred_at.isoformat() if event.occurred_at else None,
        "location": event.location or None,
        "destination": event.destination or None,
    }


class CorreiosPackageSensor(CorreiosEntity, SensorEntity):
    """Status de rastreamento mais recente de um pacote, nomeado pelo seu código."""

    _attr_translation_key = "package"
    _unrecorded_attributes = frozenset({"events"})

    def __init__(
        self,
        coordinator: CorreiosDataUpdateCoordinator,
        tracking_code: str,
    ) -> None:
        """Inicializa."""
        super().__init__(coordinator)
        self._tracking_code = tracking_code
        self._attr_translation_placeholders = {"tracking_code": tracking_code}

    @property
    def unique_id(self) -> str:
        """Retorna um unique id derivado do id da entry e do código de rastreamento."""
        return package_sensor_unique_id(
            self.coordinator.config_entry.entry_id, self._tracking_code
        )

    @property
    def package(self) -> CorreiosPackage | None:
        """Retorna o pacote que este sensor acompanha, enquanto ele for rastreado."""
        return self.packages.get(self._tracking_code)

    @property
    def available(self) -> bool:
        """Fica indisponível quando o pacote deixa de ser rastreado."""
        return super().available and self.package is not None

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
            "location": package.location or None,
            "category": package.category or None,
            "expected_delivery": package.expected_delivery.isoformat()
            if package.expected_delivery
            else None,
            "last_event_at": package.last_event_at.isoformat()
            if package.last_event_at
            else None,
            "events": [_event_attributes(event) for event in package.events],
        }
