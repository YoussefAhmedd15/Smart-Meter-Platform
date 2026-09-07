from pydantic import BaseModel
from typing import List, Optional, Any
from datetime import datetime


class UserRegisterRequest(BaseModel):
    # Plain str, not EmailStr — EmailStr needs the optional email-validator
    # package, which isn't a dependency here. Matches users.py's own
    # validation (non-empty, case-normalized), not stricter than it.
    #
    # No `role` field, deliberately. Public self-registration must never let
    # a caller choose their own role (e.g. {"role": "admin"}) — the endpoint
    # that uses this schema hardcodes the non-privileged default instead.
    # Elevated-role account creation belongs behind an authenticated
    # admin-only endpoint, not here.
    email: str
    password: str


class UserLoginRequest(BaseModel):
    email: str
    password: str


class UserPublicResponse(BaseModel):
    """A User's public fields — never password_hash or api_token_hash."""
    user_id: int
    email: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class MeterBase(BaseModel):
    meter_number: str
    meter_type: Optional[str] = None
    meter_model: str = "AM550-TD1"
    manufacturer: str = "Iskraemeco"
    firmware_version: str = "v3.14.2"
    hardware_revision: str = "HW-2.1"
    communication_interface: str = "HDLC_WITH_MODE_E"


class MeterCreate(MeterBase):
    pass


class MeterResponse(BaseModel):
    meter_id: int
    meter_number: str
    meter_type: Optional[str] = None
    meter_model: str
    manufacturer: str
    firmware_version: Optional[str] = None
    hardware_revision: str
    communication_interface: str
    status: str
    first_seen: datetime
    last_seen: datetime

    class Config:
        from_attributes = True


class ReadingResponse(BaseModel):
    meter_reading_id: int
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
    suite_id: int
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
    suite_id: Optional[int] = None
    name: str
    description: str = ""
    priority: str = "HIGH"
    obis_target: str = "1.0.1.8.0.255"
    action: str = "READ_OBIS"
    expected_result: Optional[str] = None
    timeout_ms: int = 5000
    test_steps: List[TestStep] = []
    is_active: bool = True


class TestCaseUpdate(BaseModel):
    suite_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    obis_target: Optional[str] = None
    action: Optional[str] = None
    expected_result: Optional[str] = None
    timeout_ms: Optional[int] = None
    test_steps: Optional[List[TestStep]] = None
    is_active: Optional[bool] = None


class TestCaseResponse(BaseModel):
    test_case_id: int
    suite_id: Optional[int] = None
    name: str
    description: Optional[str] = None
    priority: str
    obis_target: Optional[str] = None
    action: str
    expected_result: Optional[str] = None
    timeout_ms: int
    test_steps: List[Any] = []
    is_active: bool
    azure_test_case_id: Optional[int] = None
    azure_sync_status: str = "PENDING"
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
    
    
    
class KPISummaryResponse(BaseModel):
    total_test_executions: int
    total_meters_tested: int
    overall_pass_rate: float
    quality_score: float
    passed_tests: int
    failed_tests: int
    pending_tests: int
    avg_duration_seconds: float

class DailyTrendPoint(BaseModel):
    date: str
    total_runs: int
    passed: int
    failed: int
    pass_rate: float

class TrendsResponse(BaseModel):
    trends: List[DailyTrendPoint]
    top_failing_tests: List[Any]

class RegressionDetail(BaseModel):
    test_case_id: int
    test_name: str
    status_firmware_a: str
    status_firmware_b: str

class FirmwareComparisonResponse(BaseModel):
    firmware_a: str
    firmware_b: str
    pass_rate_a: float
    pass_rate_b: float
    pass_rate_delta: float
    regressions_detected: int
    regressed_tests: List[RegressionDetail]
    handoff_payload: Any
