"""Automated tests for Phase 4 & 5: Gemini RAG & Account-Grounded Chat."""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.rag_service import rag_service
from backend.services.gemini_service import gemini_service
from backend.models.chat import ChatMessage, ChatRequest

client = TestClient(app)


def test_query_classification():
    """Verify that query intent is classified correctly."""
    assert rag_service._classify_query("How does Furina's burst work?") == "general"
    assert rag_service._classify_query("Is my Arlecchino build good?") == "account"
    assert rag_service._classify_query("how is my kazuha") == "account"
    assert rag_service._classify_query("What is the best weapon for Nahida?") == "general"


def test_character_detection():
    """Verify that canonical character names are detected in queries."""
    assert rag_service._detect_character("Should I pull for Arlecchino?") == "Arlecchino"
    assert rag_service._detect_character("how is my Furina?") == "Furina"
    assert rag_service._detect_character("Is Bennett C6 good?") == "Bennett"
    assert rag_service._detect_character("How is Neuvillette?") == "Neuvillette"
    assert rag_service._detect_character("what is the best weapon for kleee") == "Klee"
    # Unmatched character
    assert rag_service._detect_character("What is the best artifact set?") is None


@pytest.mark.anyio
@patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
async def test_rag_general_generation(mock_generate):
    """Verify that general RAG queries retrieve documents and call Gemini."""
    mock_generate.return_value = "Golden Troupe is Furina's best artifact set."

    messages = [
        ChatMessage(role="user", content="How to build Furina?")
    ]
    
    response = await rag_service.generate_response(messages=messages)
    
    assert response.intent == "general"
    assert "Golden Troupe" in response.content
    assert len(response.citations) > 0
    # Confirm correct citation topic/character is retrieved in results
    assert any(c.character == "Furina" for c in response.citations)
    mock_generate.assert_called_once()


@pytest.mark.anyio
@patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
async def test_rag_falls_back_when_gemini_is_busy(mock_generate):
    """Verify that transient Gemini overloads still return a grounded fallback."""
    mock_generate.return_value = "Error from Gemini API: This model is currently experiencing high demand."

    messages = [
        ChatMessage(role="user", content="What is the best weapon for kleee?")
    ]

    response = await rag_service.generate_response(messages=messages)

    assert response.intent == "general"
    assert "temporarily busy" in response.content.lower()
    assert "error from gemini api" not in response.content.lower()
    assert len(response.citations) > 0


@pytest.mark.anyio
@patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock)
async def test_rag_account_generation(mock_generate):
    """Verify that account-grounded queries load character details and evaluate build."""
    mock_generate.return_value = "Your Arlecchino has high CRIT DMG, but is missing ATK."

    messages = [
        ChatMessage(role="user", content="Is my Arlecchino build good?")
    ]
    
    # Using mock UID 817739968 (which is loaded in cached/raw files)
    response = await rag_service.generate_response(messages=messages, uid="817739968")
    
    assert response.intent == "account"
    assert "Arlecchino" in response.content
    mock_generate.assert_called_once()


def test_api_chat_endpoint():
    """Verify POST /api/chat endpoint returns expected response format and citations."""
    with patch("backend.services.gemini_service.gemini_service.generate_content", new_callable=AsyncMock) as mock_generate:
        mock_generate.return_value = "Mocked chat response."

        payload = {
            "messages": [
                {"role": "user", "content": "How does Raiden Shogun perform?"}
            ],
            "uid": "817739968"
        }
        
        response = client.post("/api/chat", json=payload)
        assert response.status_code == 200
        
        data = response.json()
        assert "content" in data
        assert data["content"] == "Mocked chat response."
        assert "intent" in data
        assert "citations" in data
        assert len(data["citations"]) > 0
