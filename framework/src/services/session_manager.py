from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Optional


@dataclass
class AISession:
    account_id: str
    session_id: str
    created_at: datetime
    live_url: Optional[str] = None


class AISessionRegistry:
    def __init__(self):
        self._sessions: Dict[str, AISession] = {}

    def register(self, session: AISession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> Optional[AISession]:
        return self._sessions.get(session_id)

    def by_account(self, account_id: str) -> Optional[AISession]:
        for s in self._sessions.values():
            if s.account_id == account_id:
                return s
        return None

    def close(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)


