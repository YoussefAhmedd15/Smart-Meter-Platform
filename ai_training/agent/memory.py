from typing import Optional, Dict, Any, List
from .models import CaseState


class CaseMemory:
    """
    Manages conversational case state and persistent multi-turn memory.
    Ensures that partial facts accumulate without resetting, tracks what the user
    does not know, and preserves context across turns.
    """

    def __init__(self):
        self.state = CaseState()
        self.history: List[Dict[str, str]] = []

    def reset(self) -> None:
        """Reset the case state for a brand new customer conversation."""
        self.state = CaseState()
        self.history = []

    def get_state(self) -> CaseState:
        return self.state

    def get_state_dict(self) -> Dict[str, Any]:
        return self.state.model_dump()

    def add_user_message(self, message: str) -> None:
        self.state.last_user_message = message
        self.history.append({"role": "user", "content": message})
        self._update_summary()

    def add_agent_message(
        self,
        message: str,
        question: Optional[str] = None,
        question_field: Optional[str] = None,
    ) -> None:
        self.state.last_agent_message = message
        self.state.last_question = question
        self.state.last_question_field = question_field
        if question_field and question_field not in self.state.asked_topics:
            self.state.asked_topics.append(question_field)
        self.history.append({"role": "agent", "content": message})
        self._update_summary()

    def record_asked_topic(self, topic: str) -> None:
        if topic and topic not in self.state.asked_topics:
            self.state.asked_topics.append(topic)

    def update_facts(self, facts: Dict[str, Any]) -> None:
        """
        Merge new facts into case memory.
        Crucial rule: Never overwrite an existing known fact with None or empty string.
        Do not overwrite an established issue description with a subsequent short turn.
        """
        for field, value in facts.items():
            if value is None or (isinstance(value, str) and not value.strip()):
                continue

            # Do not overwrite an already established issue description
            if field == "issue" and self.state.issue:
                continue

            # Update specific core fields
            if hasattr(self.state, field):
                setattr(self.state, field, value)

            self.state.known_facts[field] = value

            # If user previously didn't know this and now provided it, remove from user_does_not_know
            if field in self.state.user_does_not_know:
                self.state.user_does_not_know.remove(field)

    def mark_user_does_not_know(self, fields: List[str]) -> None:
        """
        Record fields that the user explicitly stated they don't know or don't have access to.
        This guarantees the agent will never repeatedly ask for them.
        """
        for f in fields:
            if f and f not in self.state.user_does_not_know:
                self.state.user_does_not_know.append(f)

    def set_intent(self, intent: str) -> None:
        if intent:
            self.state.intent = intent

    def set_user_frustrated(self, frustrated: bool = True) -> None:
        self.state.user_frustrated = frustrated

    def set_issue(self, issue: str) -> None:
        if issue and not self.state.issue:
            self.state.issue = issue
        elif issue:
            # If new issue description is more specific, update it
            self.state.issue = issue

    def set_classification(
        self,
        category: Optional[str],
        routing: Optional[str],
        l1_status: Optional[str] = None,
    ) -> None:
        if category:
            self.state.issue_category = category
        if routing:
            self.state.routing = routing
        if l1_status:
            self.state.l1_status = l1_status

    def set_evidence(self, evidence_list: List[Dict[str, Any]]) -> None:
        self.state.evidence = evidence_list

    def _update_summary(self) -> None:
        """Generate a concise summary of the case so far."""
        parts = []
        if self.state.issue:
            parts.append(f"Issue: {self.state.issue}")
        if self.state.system:
            parts.append(f"System: {self.state.system}")
        if self.state.error_code:
            parts.append(f"Error Code: {self.state.error_code}")
        if self.state.meter_model:
            parts.append(f"Model: {self.state.meter_model}")
        if self.state.meter_type:
            parts.append(f"Type: {self.state.meter_type}")
        if self.state.scenario:
            parts.append(f"Scenario: {self.state.scenario}")
        if self.state.user_does_not_know:
            parts.append(f"User does not know: {', '.join(self.state.user_does_not_know)}")
        self.state.conversation_summary = " | ".join(parts)
