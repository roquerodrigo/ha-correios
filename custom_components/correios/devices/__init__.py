"""Dispositivos que a integração registra no device registry."""

from .account_device import CorreiosAccountDevice
from .package_device import CorreiosPackageDevice

__all__ = [
    "CorreiosAccountDevice",
    "CorreiosPackageDevice",
]
