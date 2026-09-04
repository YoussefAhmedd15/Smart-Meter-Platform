"""
Smart Meter Intelligence Platform - Meter Communication Engine.
Provides Gurux DLMS/COSEM integration and high-fidelity mock meter simulation.
"""

from .config import MeterConfig, CommunicationInterface, AuthenticationType
from .exceptions import (
    MeterCommunicationError,
    MeterTimeoutError,
    InvalidResponseError,
    SNRMFailedError,
    AARQFailedError,
    AuthenticationFailedError,
    AssociationFailedError,
    OBISNotFoundError,
    ReadFailedError,
    DecodingError,
)
from .connection import MeterConnection
from .reader import DLMSMeterReader
from .mock_meter import MockMeterAdapter

__all__ = [
    "MeterConfig",
    "CommunicationInterface",
    "AuthenticationType",
    "MeterCommunicationError",
    "MeterTimeoutError",
    "InvalidResponseError",
    "SNRMFailedError",
    "AARQFailedError",
    "AuthenticationFailedError",
    "AssociationFailedError",
    "OBISNotFoundError",
    "ReadFailedError",
    "DecodingError",
    "MeterConnection",
    "DLMSMeterReader",
    "MockMeterAdapter",
]
