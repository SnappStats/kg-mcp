"""
Gemini REST API Service - Direct REST API calls to Google Gemini with grounding support
"""
import os
import json
from typing import Dict, Any, Optional
from google.auth import default
from google.auth.transport.requests import Request
import requests


class GeminiRestService:
    """Service for making direct REST API calls to Google Gemini with grounding."""

    def __init__(self):
        """Initialize Gemini REST service with credentials."""
        self.project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        self.location = os.environ.get('GOOGLE_CLOUD_LOCATION', 'us-central1')
        # Request credentials with cloud-platform scope for Vertex AI
        self.credentials, _ = default(scopes=['https://www.googleapis.com/auth/cloud-platform'])

    def _get_access_token(self) -> str:
        """Get fresh access token for API calls."""
        if not self.credentials.valid:
            self.credentials.refresh(Request())
        return self.credentials.token

    def _resolve_refs(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve JSON Schema $refs - Gemini API doesn't support them."""
        if not isinstance(schema, dict):
            return schema

        # Extract definitions
        defs = schema.pop('$defs', {})

        def resolve(obj):
            if isinstance(obj, dict):
                if '$ref' in obj:
                    # Resolve the reference
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
        model: str = "gemini-2.0-flash-exp",
        use_grounding: bool = False,
        response_schema: Optional[Any] = None,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Make a REST API call to Gemini with optional grounding and structured output.

        Args:
            prompt: The prompt to send to the model
            model: Model name (default: gemini-2.0-flash-exp)
            use_grounding: Enable Google Search grounding for citations
            response_schema: Pydantic model for structured output
            temperature: Sampling temperature

        Returns:
            Dict with response including grounding metadata if enabled
        """
        url = (
            f"https://{self.location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{self.project_id}/locations/{self.location}/"
            f"publishers/google/models/{model}:generateContent"
        )

        headers = {
            "Authorization": f"Bearer {self._get_access_token()}",
            "Content-Type": "application/json",
        }

        # Build request body
        body = {
            "contents": [{
                "role": "user",
                "parts": [{"text": prompt}]
            }],
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": 8192,
            }
        }

        # Add grounding if enabled
        if use_grounding:
            body["tools"] = [{
                "google_search": {}
            }]

        # Add structured output schema if provided
        if response_schema:
            schema_dict = response_schema.model_json_schema()
            # Resolve $refs - Gemini doesn't support them
            schema_dict = self._resolve_refs(schema_dict)
            body["generationConfig"]["responseSchema"] = schema_dict
            body["generationConfig"]["responseMimeType"] = "application/json"

        response = requests.post(url, headers=headers, json=body, timeout=120)

        if not response.ok:
            print(f"API Error Response: {response.text}")

        response.raise_for_status()

        return response.json()

    def extract_text_from_response(self, response: Dict[str, Any]) -> str:
        """Extract text content from Gemini response."""
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
    """Get global Gemini REST service instance."""
    global _gemini_rest_service
    if _gemini_rest_service is None:
        _gemini_rest_service = GeminiRestService()
    return _gemini_rest_service
