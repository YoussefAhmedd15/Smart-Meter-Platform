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


class TestStep(BaseModel):
    action: str
    expected: str = ""


class TestSuiteCreate(BaseModel):
    name: str
    description: str = ""
    category: str = "Functional"


class TestSuiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None


class TestSuiteResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    category: str
    total_cases: int = 0
    azure_plan_id: Optional[int] = None
    azure_suite_id: Optional[int] = None
    azure_sync_status: str = "NOT_SYNCED"
    azure_sync_error: Optional[str] = None
    azure_last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TestCaseCreate(BaseModel):
    suite_id: int
    name: str
    description: str = ""
    severity: str = "HIGH"
    obis_target: str = "1.0.1.8.0.255"
    action: str = "READ_OBIS"
    expected_value: Optional[str] = None
    timeout_ms: int = 5000
    test_steps: List[TestStep] = []
    is_active: bool = True


class TestCaseUpdate(BaseModel):
    suite_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    obis_target: Optional[str] = None
    action: Optional[str] = None
    expected_value: Optional[str] = None
    timeout_ms: Optional[int] = None
    test_steps: Optional[List[TestStep]] = None
    is_active: Optional[bool] = None


class TestCaseResponse(BaseModel):
    id: int
    suite_id: int
    name: str
    description: Optional[str] = None
    severity: str
    obis_target: str
    action: str
    expected_value: Optional[str] = None
    timeout_ms: int
    test_steps: List[Any] = []
    is_active: bool
    azure_test_case_id: Optional[int] = None
    azure_sync_status: str = "NOT_SYNCED"
    azure_sync_error: Optional[str] = None
    azure_last_synced_at: Optional[datetime] = None

    class Config:
        from_attributes = True


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
