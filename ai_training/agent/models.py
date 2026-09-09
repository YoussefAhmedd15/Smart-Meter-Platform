from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field


class AgentIntent(str, Enum):
    TROUBLESHOOTING = "troubleshooting"
    ERROR_EXPLANATION = "error_explanation"
    GENERAL_QUESTION = "general_question"
    IDENTIFICATION = "identification"
    FOLLOW_UP = "follow_up"
    ESCALATION = "escalation"
    STATUS_QUESTION = "status_question"
    OTHER = "other"


class AgentAction(str, Enum):
    ANSWER = "ANSWER"
    ASK_CLARIFICATION = "ASK_CLARIFICATION"
    RETRIEVE_KNOWLEDGE = "RETRIEVE_KNOWLEDGE"
    TROUBLESHOOT = "TROUBLESHOOT"
    ESCALATE = "ESCALATE"
    ACKNOWLEDGE = "ACKNOWLEDGE"
    UNKNOWN = "UNKNOWN"


class EvidenceItem(BaseModel):
    source: str = ""
    page: Optional[int] = None
    chunk: Optional[int] = None
    evidence_type: str = "vector"  # "exact-error-code", "vector", "exact-line"
    matched_line: str = ""
    text: str = ""
    distance: float = 0.0


class CaseState(BaseModel):
    intent: Optional[str] = None
    issue: Optional[str] = None
    meter_type: Optional[str] = None
    meter_model: Optional[str] = None
    system: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    scenario: Optional[str] = None
    known_facts: Dict[str, Any] = Field(default_factory=dict)
    unknown_facts: List[str] = Field(default_factory=list)
    user_does_not_know: List[str] = Field(default_factory=list)
    conversation_summary: str = ""
    last_user_message: str = ""
    normalized_user_message: Optional[str] = None
    last_agent_message: str = ""
    last_question: Optional[str] = None
    last_question_field: Optional[str] = None
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    confidence: float = 0.0
    issue_category: Optional[str] = None
    l1_status: Optional[str] = None
    routing: Optional[str] = None
    knowledge_status: Optional[str] = None
    question_domain: Optional[str] = None
    user_frustrated: bool = False
    asked_topics: List[str] = Field(default_factory=list)
    symptom_category: Optional[str] = None
    display_symptom: Optional[str] = None


class AgentDecision(BaseModel):
    action: AgentAction = AgentAction.ANSWER
    reason: str = ""
    question: Optional[str] = None
    question_field: Optional[str] = None
    answer: Optional[str] = None
    routing: Optional[str] = None
    category: Optional[str] = None
    l1_status: Optional[str] = None
    knowledge_status: Optional[str] = None


class AgentUnderstanding(BaseModel):
    intent: str = AgentIntent.OTHER.value
    action: str = AgentAction.ANSWER.value
    issue: Optional[str] = None
    facts: Dict[str, Any] = Field(default_factory=dict)
    user_does_not_know: List[str] = Field(default_factory=list)
    needs_clarification: bool = False
    clarification_question: Optional[str] = None
    confidence: float = 0.8


class AgentResponse(BaseModel):
    text: str
    action: AgentAction
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    case_state: Optional[Dict[str, Any]] = None
    decision: Optional[Dict[str, Any]] = None
    trace: Optional[Dict[str, Any]] = None
