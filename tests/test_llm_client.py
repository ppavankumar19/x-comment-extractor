import pytest

from app.config import Settings
from app.services.llm_client import LLMClientError, NvidiaLLMClient


def build_client() -> NvidiaLLMClient:
    return NvidiaLLMClient(Settings(nvidia_api_key="test-key"))


def test_extract_json_plain_payload() -> None:
    client = build_client()
    annotation = client._parse_response(
        {
            "choices": [
                {
                    "message": {
                        "content": (
                            '{"sentiment":"positive","sentiment_score":0.9,"topics":["ai"],'
                            '"summary":"Positive comment.","language":"en","is_spam":false}'
                        )
                    }
                }
            ]
        }
    )

    assert annotation.sentiment == "positive"
    assert annotation.topics == ["ai"]


def test_extract_json_fenced_payload() -> None:
    client = build_client()
    annotation = client._parse_response(
        {
            "choices": [
                {
                    "message": {
                        "content": """```json
{"sentiment":"neutral","sentiment_score":0.4,"topics":["news"],"summary":"Neutral.","language":"en","is_spam":false}
```"""
                    }
                }
            ]
        }
    )

    assert annotation.sentiment == "neutral"


def test_extract_json_invalid_payload() -> None:
    client = build_client()
    with pytest.raises(LLMClientError):
        client._parse_response({"choices": [{"message": {"content": "not json"}}]})
