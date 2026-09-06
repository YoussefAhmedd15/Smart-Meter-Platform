import pytest
from unittest.mock import MagicMock
from backend.app.services.analytics_service import AnalyticsService

def test_quality_score_formula():
    """اختبار معادلة الجودة مع عدم وجود أعطال حرجة"""
    service = AnalyticsService(db=None)
    
   
    score = service.calculate_quality_score(pass_rate=100.0, execution_rate=100.0, critical_failures=0)
    assert score == 100.0

 
    score_with_penalty = service.calculate_quality_score(pass_rate=80.0, execution_rate=100.0, critical_failures=2)
    assert score_with_penalty == 78.0

def test_kpi_calculation_with_mocked_db():
    """اختبار سحب مؤشرات الأداء وحساب نسبة النجاح"""
    mock_db = MagicMock()
    
    
    mock_db.execute.return_value.mappings.return_value.first.return_value = {
        "total_executions": 50,
        "total_meters": 5,
        "passed_tests": 45,
        "failed_tests": 5,
        "pending_tests": 0,
        "avg_duration_seconds": 2.5
    }
   
    mock_db.execute.return_value.scalar.return_value = 0

    service = AnalyticsService(mock_db)
    kpis = service.get_overview_kpis()

    assert kpis.total_test_executions == 50
    assert kpis.overall_pass_rate == 90.0  
    assert kpis.passed_tests == 45
    assert kpis.failed_tests == 5
    assert kpis.quality_score == 94.0      