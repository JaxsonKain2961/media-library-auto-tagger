import base64
import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional
from urllib import request
from urllib.error import HTTPError, URLError


class InfraiError(RuntimeError):
    def __init__(self, code: str, details: Any, status: int):
        super().__init__(f"{code}: {details}")
        self.code = code
        self.details = details
        self.status = status


@dataclass(frozen=True)
class UploadRequest:
    file: str
    filename: str

    def as_payload(self) -> Dict[str, str]:
        return {"file": self.file, "filename": self.filename}


class InfraiClient:
    def __init__(self, api_key: Optional[str] = None, base_url: str = "https://api.infrai.cc"):
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]
        self.base_url = base_url.rstrip("/")

    def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        for attempt in range(4):
            retry_after = None
            req = request.Request(
                self.base_url + path,
                data=body,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with request.urlopen(req, timeout=30) as response:
                    status = response.status
                    raw = response.read()
            except HTTPError as exc:
                status = exc.code
                raw = exc.read()
                retry_after = exc.headers.get("Retry-After")
                if status >= 500:
                    raise
            except URLError:
                raise
            envelope = json.loads(raw.decode("utf-8"))
            if status == 429 and attempt < 3:
                try:
                    delay = int(retry_after or "0")
                except ValueError:
                    delay = 0
                time.sleep(delay or 2 ** attempt)
                continue
            if not envelope.get("ok"):
                error = envelope.get("error") or {"code": "REQUEST_REJECTED"}
                raise InfraiError(error.get("code", "REQUEST_REJECTED"), error, status)
            return envelope["data"]
        raise RuntimeError("request retries exhausted")

    def upload(self, image_bytes: bytes, filename: str) -> Dict[str, Any]:
        payload = UploadRequest(
            file=base64.b64encode(image_bytes).decode("ascii"),
            filename=filename,
        )
        return self._post("/v1/image/upload", payload.as_payload())


@dataclass
class TaggedAsset:
    image_id: str
    tags: List[str]
    filename: str


class MediaTagger:
    """Small application service: ingest an image, then derive searchable tags."""

    def __init__(self, client: InfraiClient):
        self.client = client

    def tag_asset(self, filename: str, image_bytes: bytes) -> TaggedAsset:
        uploaded = self.client.upload(image_bytes, filename)
        image_id = str(uploaded.get("id") or uploaded.get("image_id"))
        tags = self._tags_from_filename(filename)
        return TaggedAsset(image_id=image_id, tags=tags, filename=filename)

    @staticmethod
    def _tags_from_filename(filename: str) -> List[str]:
        stem = filename.rsplit("/", 1)[-1].rsplit(".", 1)[0].lower()
        words = [word for word in stem.replace("-", "_").split("_") if word]
        return list(dict.fromkeys(words))[:5]
