import os
import sys
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
    Meter, MeterReading, TestSuite, TestRun, TestResult, FailureRecord, KnowledgeItem
)
from backend.app.schemas.schemas import (
    MeterCreate, MeterResponse, ReadingResponse, TestRunCreate,
    RegressionCompareRequest, RecommendationRequest, AIChatRequest, KnowledgeItemCreate
)
from backend.app.services.meter_service import MeterService
from backend.app.services.test_service import TestEngineService
from backend.app.services.failure_service import FailureIntelligenceService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.regression_service import RegressionService
from backend.app.services.recommendation_service import RecommendationService
from backend.app.services.report_service import ReportGeneratorService
from backend.app.services.ai_service import AIService
from meter.config import MeterConfig

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
def health_check(db: Session = Depends(get_db)):
    meter_count = db.query(Meter).count()
    return {
        "status": "HEALTHY",
        "app_mode": settings.APP_MODE,
        "database": "CONNECTED",
        "total_meters": meter_count,
        "gurux_dlms_status": "INTEGRATED",
    }


# METERS ENDPOINTS
@app.get("/api/meters", response_model=List[MeterResponse])
def list_meters(db: Session = Depends(get_db)):
    meters = db.query(Meter).all()
    if not meters:
        service = MeterService(db)
        meters = [service.get_or_create_meter()]
    return meters


@app.post("/api/meters", response_model=MeterResponse)
def create_meter(data: MeterCreate, db: Session = Depends(get_db)):
    meter = Meter(**data.model_dump())
    db.add(meter)
    db.commit()
    db.refresh(meter)
    return meter


@app.get("/api/meters/{meter_id}", response_model=MeterResponse)
def get_meter(meter_id: int, db: Session = Depends(get_db)):
    meter = db.query(Meter).filter(Meter.id == meter_id).first()
    if not meter:
        raise HTTPException(status_code=404, detail="Meter not found")
    return meter


@app.get("/api/meters/{meter_id}/objects")
def get_meter_objects(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    return [obj.__dict__ for obj in service.discover_objects()]


@app.get("/api/meters/{meter_id}/readings")
def get_meter_readings(meter_id: int, db: Session = Depends(get_db)):
    readings = db.query(MeterReading).filter(MeterReading.meter_id == meter_id).all()
    if not readings:
        service = MeterService(db)
        readings = service.read_all_telemetry()
    return readings


@app.post("/api/meters/{meter_id}/connect")
def connect_meter(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    return service.connect_meter()


@app.post("/api/meters/{meter_id}/disconnect")
def disconnect_meter(meter_id: int, db: Session = Depends(get_db)):
    service = MeterService(db)
    service.reader.disconnect()
    return {"status": "DISCONNECTED", "meter_id": meter_id}


# TESTING ENDPOINTS
@app.get("/api/test-suites")
def list_test_suites(db: Session = Depends(get_db)):
    engine = TestEngineService(db)
    engine.create_default_suites()
    suites = db.query(TestSuite).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "category": s.category,
            "description": s.description,
            "total_cases": len(s.test_cases),
        }
        for s in suites
    ]


@app.post("/api/test-runs")
def start_test_run(data: TestRunCreate, db: Session = Depends(get_db)):
    engine = TestEngineService(db)
    run = engine.execute_test_run(data.meter_id, data.suite_id)
    return {
        "id": run.id,
        "status": run.status,
        "duration_seconds": run.duration_seconds,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
    }


@app.get("/api/test-runs")
def list_test_runs(db: Session = Depends(get_db)):
    runs = db.query(TestRun).order_by(TestRun.id.desc()).all()
    return [
        {
            "id": r.id,
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
    run = db.query(TestRun).filter(TestRun.id == run_id).first()
    if not run:
        raise HTTPException(status_code=404, detail="Test run not found")
    results = db.query(TestResult).filter(TestResult.test_run_id == run.id).all()
    return {
        "id": run.id,
        "status": run.status,
        "firmware_version": run.firmware_version,
        "duration_seconds": run.duration_seconds,
        "total_tests": run.total_tests,
        "passed_tests": run.passed_tests,
        "failed_tests": run.failed_tests,
        "results": [
            {
                "id": r.id,
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
    failures = db.query(FailureRecord).order_by(FailureRecord.id.desc()).all()
    return [
        {
            "id": f.id,
            "meter_id": f.meter_id,
            "firmware_version": f.firmware_version,
            "test_case": f.test_case,
            "error_type": f.error_type,
            "error_message": f.error_message,
            "severity": f.severity,
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
            "id": k.id,
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


@app.post("/api/knowledge")
def create_knowledge_item(data: KnowledgeItemCreate, db: Session = Depends(get_db)):
    item = KnowledgeItem(**data.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return item
