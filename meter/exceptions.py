class MeterCommunicationError(Exception):
    """Base exception for all DLMS/COSEM meter communication errors."""
    code: str = "COMMUNICATION_ERROR"

    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class MeterTimeoutError(MeterCommunicationError):
    """Raised when a communication timeout occurs during TX/RX."""
    code = "TIMEOUT"


class InvalidResponseError(MeterCommunicationError):
    """Raised when the meter response is malformed or invalid."""
    code = "INVALID_RESPONSE"


class SNRMFailedError(MeterCommunicationError):
    """Raised when HDLC Set Normal Response Mode (SNRM) handshake fails."""
    code = "SNRM_FAILED"


class AARQFailedError(MeterCommunicationError):
    """Raised when Application Association Request (AARQ) fails."""
    code = "AARQ_FAILED"


class AuthenticationFailedError(MeterCommunicationError):
    """Raised when DLMS authentication (Low/High) fails."""
    code = "AUTHENTICATION_FAILED"


class AssociationFailedError(MeterCommunicationError):
    """Raised when retrieving the Association View fails."""
    code = "ASSOCIATION_FAILED"


class OBISNotFoundError(MeterCommunicationError):
    """Raised when requested OBIS logical name is missing from meter's association view."""
    code = "OBJECT_NOT_FOUND"


class ReadFailedError(MeterCommunicationError):
    """Raised when reading an attribute from a COSEM object fails."""
    code = "READ_FAILED"


class DecodingError(MeterCommunicationError):
    """Raised when decoding a DLMS data structure fails."""
    code = "DECODING_ERROR"
