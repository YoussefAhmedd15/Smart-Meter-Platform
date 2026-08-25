from typing import List, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime


class AttributeDescriptor(BaseModel):
    index: int
    name: str = ""
    readable: bool = True
    writable: bool = False
    data_type: Optional[str] = None


class COSEMObjectDescriptor(BaseModel):
    class_id: int
    obis: str
    version: int = 0
    name: str = ""
    description: str = ""
    attributes: List[AttributeDescriptor] = Field(default_factory=list)
    methods: List[dict] = Field(default_factory=list)


class ReadResult(BaseModel):
    obis: str
    attribute_index: int = 2
    value: Any
    raw_value: Optional[str] = None
    unit: str = ""
    data_type: str = "Unknown"
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: float = 0.0
    status: str = "PASS"
    error_message: Optional[str] = None


class AssociationView(BaseModel):
    meter_serial: str = "UNKNOWN"
    total_objects: int = 0
    objects: List[COSEMObjectDescriptor] = Field(default_factory=list)
