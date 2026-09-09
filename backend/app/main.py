import os
import sys
import logging
from datetime import datetime
from fastapi import FastAPI, Depends, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import List, Optional

# Ensure workspace imports function cleanly
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from backend.app.core.config import settings
from backend.app.core.logging import setup_logging
from backend.app.db.database import get_db, init_db
from backend.app.db.models import (
    Meter, MeterReading, TestSuite, TestCase, TestCaseStep, TestRun, TestResult,
    FailureRecord, KnowledgeItem, Firmware
)
from backend.app.schemas.schemas import (
    MeterCreate, MeterResponse, MeterProfileResponse, ReadingResponse, TestRunCreate,
    RegressionCompareRequest, RecommendationRequest, AIChatRequest, KnowledgeItemCreate,
    TestSuiteCreate, TestSuiteUpdate, TestSuiteResponse,
    TestCaseCreate, TestCaseUpdate, TestCaseResponse,
)
from backend.app.services.meter_service import MeterService
from backend.app.services.test_service import TestEngineService
from backend.app.services.failure_service import FailureIntelligenceService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.regression_service import RegressionService
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.report_service import ReportGeneratorService
from backend.app.services.ai_service import AIService
from backend.app.services.azure_devops_service import AzureDevOpsService, AzureDevOpsError
from backend.app.api.auth import router as auth_router
from backend.app.core.dependencies import get_current_user
from meter.config import MeterConfig

logger = logging.getLogger("smart_meter_api")

setup_logging()
init_db()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    description="Smart Meter Intelligence Platform - DLMS/COSEM Test Automation, Failure Intelligence, and AI RAG System",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": getattr(exc, "code", "INTERNAL_SERVER_ERROR"),
                "message": str(exc),
                "request_id": str(id(request)),
            }
        },
    )


@app.get("/health")
@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    try:
        meter_count = db.query(Meter).count()
        db_status = "CONNECTED"
    except Exception as exc:
        meter_count = 0
        db_status = f"DISCONNECTED ({type(exc).__name__})"
    return {
        "status": "HEALTHY",
        "app_mode": settings.APP_MODE,
        "database": db_status,
        "total_meters": meter_count,
        "gurux_dlms_status": "INTEGRATED",
    }


def _get_or_create_firmware(db: Session, version_string: str) -> Firmware:
    firmware = db.query(Firmware).filter(Firmware.version == version_string).first()
    if not firmware:
        firmware = Firmware(version=version_string, status="RELEASED")
        db.add(firmware)
        db.commit()
        db.refresh(firmware)
    return firmware


# METERS ENDPOINTS
@app.get("/api/meters", response_model=List[MeterResponse])
def list_meters(
    limit: int = Query(default=100, ge=1, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    meters = db.query(Meter).offset(offset).limit(limit).all()
    if not meters and offset == 0:
        service = MeterService(db)
        meters = [service.get_or_create_meter()]
    return meters


@app.post("/api/meters", response_model=MeterResponse, dependencies=[Depends(get_current_user)])
def create_meter(data: MeterCreate, db: Session = Depends(get_db)):
    payload = data.model_dump()
    firmware_version = payload.pop("firmware_version")
    firmware = _get_or_create_firmware(db, firmware_version)
    meter = Meter(firmware_id=firmware.firmware_id, **payload)
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@app.get("/api/meters/{meter_id}", response_model=MeterResponse)
def get_meter(meter_id: int, db: Session = Depends(get_db)):
    meter = db.query(Meter).filter(Meter.meter_id == meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    return meter


@app.get("/api/meters/{meter_id}/objects")
def get_meter_objects(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    return [obj.__dict__ for obj in service.discover_objects()]


@app.get("/api/meters/{meter_id}/profile", response_model=MeterProfileResponse)
def get_meter_profile(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    profile = service.get_meter_profile(meter_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Meter not found")
    return profile


def _reading_to_dict(r: MeterReading, data_source: str) -> dict:
    return {
        "meter_reading_id": r.meter_reading_id,
        "meter_id": r.meter_id,
        "obis": r.obis,
        "attribute_index": r.attribute_index,
        "value": r.value,
        "raw_value": r.raw_value,
        "unit": r.unit,
        "data_type": r.data_type,
        "timestamp": r.timestamp.isoformat() if r.timestamp else None,
        "quality": r.quality,
        "source": r.source,
        # Real per-request value when freshly read this request; "unknown"
        # (not fabricated as mock/hardware) for rows already stored from a
        # prior request, since data_source isn't a persisted column and
        # genuinely isn't known for historical rows.
        "data_source": data_source,
    }


@app.get("/api/meters/{meter_id}/readings")
def get_meter_readings(meter_id: int, db: Session = Depends(get_db)):
    """Always takes a fresh read — this is the endpoint the Live Meter
    frontend polls on an interval, so it must return this moment's real
    telemetry (and real data_source) every call, not the first call's
    readings replayed forever. LiveMeter.tsx is the only caller of this
    endpoint (confirmed via grep) — no other consumer relies on the old
    "only refresh when the table is empty" behavior."""
    service = MeterService(db)
    fresh_readings = service.read_all_telemetry()
    return [_reading_to_dict(r, r.data_source) for r in fresh_readings]


@app.post("/api/meters/{meter_id}/connect", dependencies=[Depends(get_current_user)])
def connect_meter(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    return service.connect_meter(meter_id)


@app.post("/api/meters/{meter_id}/disconnect", dependencies=[Depends(get_current_user)])
def disconnect_meter(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)    
    return service.disconnect_meter()

def get_azure_service() -> AzureDevOpsService:
    """FastAPI dependency; overridden with a mock in tests."""
    return AzureDevOpsService()


def _suite_to_dict(suite: TestSuite) -> dict:
    return {
        "suite_id": suite.suite_id,
        "name": suite.name,
        "category": suite.category,
        "description": suite.description,
        "total_cases": len(suite.test_cases),
        "azure_plan_id": suite.azure_plan_id,
        "azure_suite_id": suite.azure_suite_id,
        "azure_sync_status": suite.azure_sync_status,
        "azure_sync_error": suite.azure_sync_error,
        "azure_last_synced_at": suite.azure_last_synced_at,
    }


def _set_test_case_steps(db: Session, test_case: TestCase, steps: List[dict]) -> None:
    """Replaces a test case's normalized `test_case_steps` rows from the API's
    [{action, expected}, ...] shape."""
    for existing in list(test_case.steps):
        db.delete(existing)
    db.flush()
    for i, step in enumerate(steps or []):
        db.add(TestCaseStep(
            test_case_id=test_case.test_case_id,
            step_number=i + 1,
            action=step.get("action", "") if isinstance(step, dict) else step.action,
            expected_result=step.get("expected", "") if isinstance(step, dict) else step.expected,
        ))


def _sync_test_case_to_azure(db: Session, test_case: TestCase, suite: TestSuite, azure: AzureDevOpsService) -> None:
    """
    Syncs a local TestCase (and its parent TestSuite, if needed) to Azure DevOps.
    Never raises: on any Azure failure the local record is kept and marked FAILED
    with the error message, so the caller can retry later via /sync-azure.
    """
    if not azure.is_configured:
        if suite is not None and suite.azure_suite_id is None:
            suite.azure_sync_status = "NOT_CONFIGURED"
        test_case.azure_sync_status = "NOT_CONFIGURED"
        test_case.azure_sync_error = None
        db.commit()
        return

    try:
        if suite.azure_suite_id is None:
            azure_suite_id = azure.get_or_create_test_suite(suite.name)
            suite.azure_suite_id = azure_suite_id
            suite.azure_plan_id = int(azure.plan_id)
            suite.azure_sync_status = "SYNCED"
            suite.azure_sync_error = None
            suite.azure_last_synced_at = datetime.utcnow()
            db.commit()

        if test_case.azure_test_case_id is None:
            azure_case_id = azure.create_test_case(
                name=test_case.name,
                description=test_case.description or "",
                test_steps=test_case.test_steps or [],
            )
            test_case.azure_test_case_id = azure_case_id
        else:
            azure.update_test_case(
                test_case.azure_test_case_id,
                name=test_case.name,
                description=test_case.description or "",
                test_steps=test_case.test_steps or [],
            )

        azure.add_test_case_to_suite(suite.azure_suite_id, test_case.azure_test_case_id)

        test_case.azure_sync_status = "SYNCED"
        test_case.azure_sync_error = None
        test_case.azure_last_synced_at = datetime.utcnow()
        logger.info(f"Test case {test_case.test_case_id} synced to Azure work item {test_case.azure_test_case_id}")
    except AzureDevOpsError as exc:
        test_case.azure_sync_status = "FAILED"
        test_case.azure_sync_error = str(exc)[:1000]
        logger.error(f"Azure sync failed for test case {test_case.test_case_id}: {exc}")

    db.commit()
    db.refresh(test_case)


# TESTING ENDPOINTS
@app.get("/api/test-suites", response_model=List[TestSuiteResponse])
def list_test_suites(db: Session = Depends(get_db)):
    engine = TestEngineService(db)
    engine.create_default_suites()
    suites = db.query(TestSuite).all()
    return [_suite_to_dict(s) for s in suites]


@app.post("/api/test-suites", response_model=TestSuiteResponse, status_code=201, dependencies=[Depends(get_current_user)])
def create_test_suite(data: TestSuiteCreate, db: Session = Depends(get_db)):
    suite = TestSuite(**data.model_dump())
    db.add(suite)
    db.commit()
    db.refresh(suite)
    return _suite_to_dict(suite)


@app.put("/api/test-suites/{suite_id}", response_model=TestSuiteResponse, dependencies=[Depends(get_current_user)])
def update_test_suite(suite_id: int, data: TestSuiteUpdate, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.suite_id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(suite, field, value)
    db.commit()
    db.refresh(suite)
    return _suite_to_dict(suite)


@app.delete("/api/test-suites/{suite_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_test_suite(suite_id: int, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.suite_id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Test suite not found")
    db.delete(suite)
    db.commit()
    return None


# TEST CASE ENDPOINTS (local CRUD + Azure DevOps Test Plans sync)
@app.post("/api/test-cases", response_model=TestCaseResponse, status_code=201, dependencies=[Depends(get_current_user)])
def create_test_case(
    data: TestCaseCreate,
    db: Session = Depends(get_db),
    azure: AzureDevOpsService = Depends(get_azure_service),
):
    suite = None
    if data.suite_id is not None:
        suite = db.query(TestSuite).filter(TestSuite.suite_id == data.suite_id).first()
        if not suite:
            raise HTTPException(status_code=404, detail="Test suite not found")

    payload = data.model_dump()
    steps = payload.pop("test_steps", [])
    test_case = TestCase(**payload)
    db.add(test_case)
    db.commit()
    db.refresh(test_case)

    _set_test_case_steps(db, test_case, steps)
    db.commit()
    db.refresh(test_case)

    if suite is not None:
        _sync_test_case_to_azure(db, test_case, suite, azure)
    return test_case


@app.get("/api/test-cases", response_model=List[TestCaseResponse])
def list_test_cases(suite_id: Optional[int] = Query(None), db: Session = Depends(get_db)):
    query = db.query(TestCase)
    if suite_id is not None:
        query = query.filter(TestCase.suite_id == suite_id)
    return query.order_by(TestCase.test_case_id.desc()).all()


@app.get("/api/test-cases/{case_id}", response_model=TestCaseResponse)
def get_test_case(case_id: int, db: Session = Depends(get_db)):
    test_case = db.query(TestCase).filter(TestCase.test_case_id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    return test_case


@app.put("/api/test-cases/{case_id}", response_model=TestCaseResponse, dependencies=[Depends(get_current_user)])
def update_test_case(
    case_id: int,
    data: TestCaseUpdate,
    db: Session = Depends(get_db),
    azure: AzureDevOpsService = Depends(get_azure_service),
):
    test_case = db.query(TestCase).filter(TestCase.test_case_id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")

    updates = data.model_dump(exclude_unset=True)
    steps = updates.pop("test_steps", None)

    target_suite_id = updates.get("suite_id", test_case.suite_id)
    suite = None
    if target_suite_id is not None:
        suite = db.query(TestSuite).filter(TestSuite.suite_id == target_suite_id).first()
        if not suite:
            raise HTTPException(status_code=404, detail="Test suite not found")

    for field, value in updates.items():
        setattr(test_case, field, value)
    test_case.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(test_case)

    if steps is not None:
        _set_test_case_steps(db, test_case, steps)
        db.commit()
        db.refresh(test_case)

    if suite is not None:
        _sync_test_case_to_azure(db, test_case, suite, azure)
    return test_case


@app.delete("/api/test-cases/{case_id}", status_code=204, dependencies=[Depends(get_current_user)])
def delete_test_case(case_id: int, db: Session = Depends(get_db)):
    test_case = db.query(TestCase).filter(TestCase.test_case_id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    db.delete(test_case)
    db.commit()
    return None


@app.post("/api/test-cases/{case_id}/sync-azure", response_model=TestCaseResponse, dependencies=[Depends(get_current_user)])
def retry_sync_test_case(
    case_id: int,
    db: Session = Depends(get_db),
    azure: AzureDevOpsService = Depends(get_azure_service),
):
    test_case = db.query(TestCase).filter(TestCase.test_case_id == case_id).first()
    if not test_case:
        raise HTTPException(status_code=404, detail="Test case not found")
    suite = db.query(TestSuite).filter(TestSuite.suite_id == test_case.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="Parent test suite not found")
    _sync_test_case_to_azure(db, test_case, suite, azure)
    return test_case


@app.post("/api/test-runs", dependencies=[Depends(get_current_user)])
def start_test_run(data: TestRunCreate, db: Session = Depends(get_db)):
    engine = TestEngineService(db)
    run = engine.execute_test_run(data.meter_id, data.suite_id)
    return {
        "id": run.test_run_id,
        "status": run.status,
        "duration_seconds": run.duration_seconds,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
    }


@app.get("/api/test-runs")
def list_test_runs(db: Session = Depends(get_db)):
    runs = db.query(TestRun).order_by(TestRun.test_run_id.desc()).all()
    return [
        {
            "id": r.test_run_id,
            "meter_id": r.meter_id,
            "firmware_version": r.firmware_version,
            "status": r.status,
            "total_tests": r.total_tests,
            "passed_tests": r.passed_tests,
            "failed_tests": r.failed_tests,
            "duration_seconds": r.duration_seconds,
            "started_at": r.started_at.isoformat() if r.started_at else None,
        }
        for r in runs
    ]


@app.get("/api/test-runs/{run_id}")
def get_test_run_details(run_id: int, db: Session = Depends(get_db)):
    run = db.query(TestRun).filter(TestRun.test_run_id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    results = db.query(TestResult).filter(TestResult.test_run_id == run.test_run_id).all()
    return {
        "id": run.test_run_id,
        "status": run.status,
        "firmware_version": run.firmware_version,
        "duration_seconds": run.duration_seconds,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
        "results": [
            {
                "id": r.test_result_id,
                "test_name": r.test_name,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "actual_value": r.actual_value,
                "error_message": r.error_message,
            }
            for r in results
        ]
    }


# FAILURES ENDPOINTS
@app.get("/api/failures")
def list_failures(db: Session = Depends(get_db)):
    failures = db.query(FailureRecord).order_by(FailureRecord.failure_id.desc()).all()
    return [
        {
            "id": f.failure_id,
            "meter_id": f.meter_id,
            "firmware_version": f.firmware_version,
            "test_case": f.test_case_name,
            "error_type": f.error_code,
            "error_message": f.case_details,
            "severity": f.case_severity,
            "created_at": f.created_at.isoformat() if f.created_at else None,
        }
        for f in failures
    ]


@app.get("/api/failures/{failure_id}/similar")
def get_similar_failures(failure_id: int, db: Session = Depends(get_db)):
    service = FailureIntelligenceService(db)
    return service.analyze_failure(failure_id)


# ANALYTICS ENDPOINTS
@app.get("/api/analytics/overview")
def get_analytics_overview(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_overview_kpis()


@app.get("/api/analytics/firmware")
def get_analytics_firmware(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_failures_by_firmware()


@app.get("/api/analytics/models")
def get_analytics_models(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_failures_by_model()


@app.get("/api/analytics/trends")
def get_analytics_trends(db: Session = Depends(get_db)):
    service = AnalyticsService(db)
    return service.get_test_trends()


# REGRESSION ENDPOINTS
@app.post("/api/regression/compare")
def compare_regression(data: RegressionCompareRequest, db: Session = Depends(get_db)):
    service = RegressionService(db)
    return service.compare_firmware_versions(data.firmware_a, data.firmware_b)


# RECOMMENDATIONS ENDPOINTS
@app.post("/api/recommendations/tests")
def recommend_tests(data: RecommendationRequest, db: Session = Depends(get_db)):
    service = RecommendationService(db)
    return service.recommend_regression_suite(data.change_summary)


# AI ENDPOINTS
@app.post("/api/ai/chat")
def ai_chat(data: AIChatRequest, db: Session = Depends(get_db)):
    service = AIService(db)
    return service.ask_ai(data.question)


# REPORTS ENDPOINTS
@app.post("/api/reports/test-run/{run_id}")
def generate_report(run_id: int, format_type: str = Query("pdf"), db: Session = Depends(get_db)):
    service = ReportGeneratorService(db)
    return service.generate_test_run_report(run_id, format_type)


@app.get("/api/reports/download/{filename}")
def download_report(filename: str):
    output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/reports"))
    filepath = os.path.join(output_dir, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Report file not found")
    return FileResponse(filepath, media_type="application/json", filename=filename)


# KNOWLEDGE BASE ENDPOINTS
@app.get("/api/knowledge")
def list_knowledge_items(db: Session = Depends(get_db)):
    items = db.query(KnowledgeItem).all()
    return [
        {
            "id": k.knowledge_item_id,
            "title": k.title,
            "problem": k.problem,
            "symptoms": k.symptoms,
            "affected_models": k.affected_models,
            "firmware": k.firmware,
            "root_cause": k.root_cause,
            "solution": k.solution,
            "fixed_version": k.fixed_version,
            "severity": k.severity,
            "tags": k.tags,
        }
        for k in items
    ]


@app.post("/api/knowledge", dependencies=[Depends(get_current_user)])
def create_knowledge_item(data: KnowledgeItemCreate, db: Session = Depends(get_db)):
    item = KnowledgeItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
