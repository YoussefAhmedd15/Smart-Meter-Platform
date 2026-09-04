from abc import ABC, abstractmethod
from typing import Optional, Any
from .config import MeterConfig, CommunicationInterface
from .exceptions import MeterCommunicationError, MeterTimeoutError


class MeterConnection(ABC):
    """Abstract interface for smart meter transport connection layer."""

    def __init__(self, config: MeterConfig):
        self.config = config
        self._is_connected: bool = False

    @abstractmethod
    def connect(self) -> bool:
        """Establish physical media connection."""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Close physical media connection."""
        pass

    def is_connected(self) -> bool:
        """Check connection status."""
        return self._is_connected

    @abstractmethod
    def send(self, data: bytes) -> int:
        """Send raw byte stream over media."""
        pass

    @abstractmethod
    def receive(self, max_bytes: int = 1024, timeout_ms: Optional[int] = None) -> bytes:
        """Receive byte stream from media."""
        pass
