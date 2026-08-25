from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class MeterBase(BaseModel):
    serial_number: str
    manufacturer: str = "Iskraemeco"
    model: str = "AM550-TD1"
    firmware_version: str = "v3.14.2"
    hardware_revision: str = "HW-2.1"
    communication_interface: str = "HDLC_WITH_MODE_E"


class MeterCreate(MeterBase):
    pass


class MeterResponse(MeterBase):
    id: int
    status: str
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class ReadingResponse(BaseModel):
    id: int
    meter_id: int
    obis: str
    attribute_index: int
    value: str
    raw_value: Optional[str] = None
    unit: str
    data_type: str
    timestamp: datetime
    quality: str
    source: str

    class Config:
        from_attributes = True


class TestRunCreate(BaseModel):
    meter_id: int
    suite_id: int


class RegressionCompareRequest(BaseModel):
    firmware_a: str = "v3.13.0"
    firmware_b: str = "v3.14.2"


class RecommendationRequest(BaseModel):
    change_summary: str = "Modified Load Profile Generic buffer allocation and Mode E optical probe handshake"


class AIChatRequest(BaseModel):
    question: str = "Why did meter ISK-2026-984210 fail during load profile test?"


class KnowledgeItemCreate(BaseModel):
    title: str
    problem: str
    symptoms: str
    affected_models: str = "Iskraemeco AM550"
    firmware: str = "v3.12 - v3.14"
    root_cause: str
    solution: str
    fixed_version: str = "v3.15.0"
    severity: str = "HIGH"
    tags: str = "HDLC, Mode E"
