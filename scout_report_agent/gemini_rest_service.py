import os
import json
import tempfile
import requests
from typing import Dict, Any, Optional
from google.auth import default
from google.auth.transport.requests import Request
from logger import logger


class GeminiRestService:
    def __init__(self):
        if 'API_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS' in os.environ:
            creds_json = json.loads(os.environ['API_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS'])
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(creds_json, f)
                os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name

        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])

    def _get_access_token(self) -> str:
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def _resolve_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(schema, dict):
            return schema

        defs = schema.pop('$defs', {})

        def resolve(obj):
            if isinstance(obj, dict):
                if '$ref' in obj:
                    ref_path = obj['$ref'].split('/')
                    if ref_path[0] == '#' and ref_path[1] == '$defs':
                        def_name = ref_path[2]
                        if def_name in defs:
                            return resolve(defs[def_name].copy())
                    return obj
                else:
                    return {k: resolve(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [resolve(item) for item in obj]
            else:
                return obj

        return resolve(schema)

    def make_ai_call(
        self,
        prompt: str,
        model: str = "gemini-2.5-flash",
        use_grounding: bool = False,
        response_schema: Optional[Any] = None,
        temperature: float = 0.1,
    ) -> Dict[str, Any]:
        url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/{model}:generateContent"
        )

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

        body = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 40000,
            }
        }

        if use_grounding:
            body["tools"] = [{
                "googleSearch": {}
            }]

        if response_schema:
            schema_dict = response_schema.model_json_schema()
            schema_dict = self._resolve_refs(schema_dict)
            body["generationConfig"]["responseSchema"] = schema_dict
            body["generationConfig"]["responseMimeType"] = "application/json"

        response = requests.post(url, headers=headers, json=body, timeout=300)

        if not response.ok:
            logger.error(f"google api error raised: {response.text}")

        response.raise_for_status()

        return response.json()

    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        try:
            candidates = response.get('candidates', [])
            if not candidates:
                return ""

            content = candidates[0].get('content', {})
            parts = content.get('parts', [])
            if not parts:
                return ""

            return parts[0].get('text', '')
        except Exception:
            return ""


_gemini_rest_service = None


def get_gemini_rest_service() -> GeminiRestService:
    global _gemini_rest_service
    if _gemini_rest_service is None:
        _gemini_rest_service = GeminiRestService()
    return _gemini_rest_service
