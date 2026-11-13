import json

import httpx


class KeitaroError(Exception):
    def __init__(self, status: int, message: str) -> None:
        self.status = status
        self.message = message
        super().__init__(message)


class KeitaroClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        self._base = f"{base_url.rstrip('/')}/admin_api/v1"
        self._headers = {"Api-Key": api_key, "Accept": "application/json"}

    def campaigns(self) -> list[dict]:
        return self._request("GET", "/campaigns")

    def campaign(self, campaign_id: int) -> dict:
        return self._request("GET", f"/campaigns/{campaign_id}")

    def create_campaign(self, payload: dict) -> dict:
        return self._request("POST", "/campaigns", json=payload)

    def delete_campaign(self, campaign_id: int) -> dict | None:
        return self._request("DELETE", f"/campaigns/{campaign_id}")

    def domains(self) -> list[dict]:
        return self._request("GET", "/domains")

    def groups(self) -> list[dict]:
        return self._request("GET", "/groups", params={"type": "campaigns"})

    def traffic_sources(self) -> list[dict]:
        return self._request("GET", "/traffic_sources")

    def offers(self) -> list[dict]:
        return self._request("GET", "/offers")

    def offer(self, offer_id: int) -> dict:
        return self._request("GET", f"/offers/{offer_id}")

    def campaign_streams(self, campaign_id: int) -> list[dict]:
        return self._request("GET", f"/campaigns/{campaign_id}/streams")

    def stream(self, stream_id: int) -> dict:
        return self._request("GET", f"/streams/{stream_id}")

    def create_stream(self, payload: dict) -> dict:
        return self._request("POST", "/streams", json=payload)

    def update_stream(self, stream_id: int, payload: dict) -> dict:
        return self._request("PUT", f"/streams/{stream_id}", json=payload)

    def report(self, payload: dict) -> dict:
        return self._request("POST", "/report/build", json=payload)

    def _request(self, method: str, path: str, **kwargs):
        with httpx.Client(timeout=30) as client:
            response = client.request(method, f"{self._base}{path}", headers=self._headers, **kwargs)
        if response.status_code >= 400:
            raise KeitaroError(response.status_code, _error_message(response))
        if not response.content:
            return None
        return response.json()


def _error_message(response: httpx.Response) -> str:
    try:
        body = response.json()
    except json.JSONDecodeError:
        return response.text or response.reason_phrase
    if isinstance(body, dict):
        message = body.get("error") or body.get("message") or body.get("detail") or body
    else:
        message = body
    if isinstance(message, (dict, list)):
        return json.dumps(message, ensure_ascii=False)
    return str(message)
