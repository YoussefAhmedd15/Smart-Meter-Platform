from typing import Optional, Dict, Any
from .agent import L1Agent
from .models import AgentResponse


class ConversationManager:
    """
    Manages conversational session lifecycle, command dispatch,
    and formatted dialogue interactions.
    """

    def __init__(self, agent: Optional[L1Agent] = None):
        self.agent = agent or L1Agent()

    def start_new_case(self) -> None:
        """Reset agent memory and begin a fresh customer support session."""
        self.agent.reset()

    def get_case_state(self) -> Dict[str, Any]:
        """Return the current structured case state dictionary."""
        return self.agent.get_state().model_dump()

    def handle_message(self, message: str) -> AgentResponse:
        """Process incoming customer message and return agent response."""
        return self.agent.process_message(message)
