import asyncio
import base64
import io
import logging
from datetime import datetime
from typing import Dict, Optional, Set


logger = logging.getLogger(__name__)

try:
    from PIL import Image  # type: ignore
except Exception:  # pragma: no cover
    Image = None  # type: ignore


class LiveMonitoringService:
    def __init__(self):
        self.active_sessions: Dict[str, Dict] = {}
        self.websocket_clients: Set = set()

    async def start_monitoring_session(self, account_id: str, session_id: str, live_url: Optional[str]):
        self.active_sessions[account_id] = {
            "session_id": session_id,
            "live_url": live_url,
            "status": "active",
            "start_time": datetime.utcnow().isoformat(),
        }

    async def capture_screenshot_webp(self, stagehand_page) -> Optional[str]:
        try:
            if Image is None:
                return None
            raw = await stagehand_page.screenshot(type="png")
            img = Image.open(io.BytesIO(raw))
            img = img.resize((800, 600))
            buf = io.BytesIO()
            img.save(buf, format="WEBP", quality=70)
            return base64.b64encode(buf.getvalue()).decode()
        except Exception as exc:  # pragma: no cover
            logger.error("Screenshot capture failed: %s", exc)
            return None


