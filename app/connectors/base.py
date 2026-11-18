from abc import ABC, abstractmethod
from typing import Dict, Any
from fastapi import HTTPException

class ConnectorError(Exception):
    def __init__(self, code: str, message: str, retryable: bool = False, details: Dict[str, Any] = None):
        self.code = code
        self.message = message
        self.retryable = retryable
        self.details = details or {}
        super().__init__(message)

class BaseConnector(ABC):
    connector_key: str = "base"

    def map_http_error(self, status_code: int, raw_message: str = "", reset_after_s: int = 60) -> ConnectorError:
        if status_code == 429:
            return ConnectorError("PLATFORM_RATE_LIMIT", f"Rate limited. Retry after {reset_after_s}s.", retryable=True, details={"reset_after_s": reset_after_s})
        if status_code in (401, 403):
            return ConnectorError("CONNECTION_AUTH_EXPIRED", "Token expired or revoked. Please reconnect.", retryable=False)
        if status_code in (400, 422):
            return ConnectorError("PLATFORM_CONTENT_REJECTED", f"Platform rejected content: {raw_message}", retryable=False)
        if status_code >= 500:
            return ConnectorError("PLATFORM_UNAVAILABLE", "Upstream platform error.", retryable=True)
        return ConnectorError("PLATFORM_CONTENT_REJECTED", raw_message, retryable=False)

    @abstractmethod
    def validate(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def publish(self, rendition: Dict[str, Any], destination: Dict[str, Any], connection: Dict[str, Any], idempotency_key: str) -> Dict[str, Any]:
        pass

    @abstractmethod
    def get_status(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        pass

    @abstractmethod
    def delete(self, platform_post_id: str, connection: Dict[str, Any]) -> Dict[str, Any]:
        pass

    def fetch_metrics(self, platform_post_id: str, connection: Dict[str, Any], since: str = None) -> Dict[str, Any]:
        return {"views": 0, "likes": 0, "comments": 0, "shares": 0, "saves": 0, "watch_time_s": 0, "clicks": 0}

    def refresh_auth(self, connection: Dict[str, Any]) -> Dict[str, Any]:
        return {"expires_at": "2027-01-01T00:00:00Z"}

    def build_assist_pack(self, rendition: Dict[str, Any], destination: Dict[str, Any]) -> Dict[str, Any]:
        raise ConnectorError("DEST_SPEC_VIOLATION", f"{self.connector_key} does not support assisted packs.", retryable=False)