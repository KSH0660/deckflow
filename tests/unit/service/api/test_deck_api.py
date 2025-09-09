"""Tests for deck API endpoints - separate from orchestration logic."""

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_deck_service():
    """Mock the DeckService."""
    from app.api.deck import get_deck_service
    from app.models.responses.deck import CreateDeckResponse

    service = AsyncMock()
    service.create_deck.return_value = CreateDeckResponse(
        deck_id=str(uuid4()), status="generating"
    )

    # Override the FastAPI dependency
    app.dependency_overrides[get_deck_service] = lambda: service
    yield service

    # Clean up after the test
    if get_deck_service in app.dependency_overrides:
        del app.dependency_overrides[get_deck_service]


@pytest.fixture
def mock_deck_service_comprehensive():
    """Mock the DeckService with comprehensive responses."""
    from datetime import datetime

    from app.api.deck import get_deck_service
    from app.models.responses.deck import (
        CreateDeckResponse,
        DeckListItemResponse,
        DeckStatusResponse,
        ModifySlideResponse,
    )

    service = AsyncMock()

    # Setup all the common mock responses
    deck_id = str(uuid4())
    service.create_deck.return_value = CreateDeckResponse(
        deck_id=deck_id, status="generating"
    )
    service.get_deck_status.return_value = DeckStatusResponse(
        deck_id=deck_id,
        status="completed",
        slide_count=1,
        created_at=datetime(2024, 1, 1),
        updated_at=None,
        completed_at=datetime(2024, 1, 1, 0, 5),
    )
    service.modify_slide.return_value = ModifySlideResponse(
        deck_id=deck_id, slide_order=1, status="modifying"
    )
    service.list_decks.return_value = [
        DeckListItemResponse(
            deck_id=deck_id,
            title="Test Deck",
            status="completed",
            slide_count=1,
            created_at=datetime(2024, 1, 1),
        )
    ]
    service.get_deck_data.return_value = {"deck_id": deck_id, "title": "Test"}
    service.delete_deck.return_value = {"status": "success"}

    # Override dependency
    app.dependency_overrides[get_deck_service] = lambda: service
    yield service

    # Clean up
    if get_deck_service in app.dependency_overrides:
        del app.dependency_overrides[get_deck_service]


class TestDeckAPIEndpoints:
    """Test API endpoints separately from business logic."""

    def test_create_deck_api_contract(self, client, mock_deck_service):
        """Test deck creation API contract."""
        request_data = {
            "prompt": "Create a test presentation about API testing",
            "style": {"theme": "professional"},
            "files": None,
        }

        response = client.post("/api/decks", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "deck_id" in response_data
        assert "status" in response_data
        assert response_data["status"] == "generating"

        # Verify service was called
        mock_deck_service.create_deck.assert_called_once()

    def test_create_deck_validation(self, client):
        """Test API request validation."""
        # Missing prompt
        response = client.post("/api/decks", json={})
        assert response.status_code == 422

        # Prompt too short
        response = client.post("/api/decks", json={"prompt": "Hi"})  # < 5 chars
        assert response.status_code == 422

        # Prompt too long
        long_prompt = "x" * 5001  # > 5000 chars
        response = client.post("/api/decks", json={"prompt": long_prompt})
        assert response.status_code == 422

    def test_get_deck_status_api(self, client):
        """Test deck status retrieval API."""
        from datetime import datetime

        from app.api.deck import get_deck_service
        from app.models.responses.deck import DeckStatusResponse

        deck_id = str(uuid4())

        # Create mock service
        mock_service = AsyncMock()
        mock_service.get_deck_status.return_value = DeckStatusResponse(
            deck_id=deck_id,
            status="completed",
            slide_count=1,
            created_at=datetime(2024, 1, 1, 0, 0, 0),
            updated_at=None,
            completed_at=datetime(2024, 1, 1, 0, 5, 0),
        )

        # Override dependency
        app.dependency_overrides[get_deck_service] = lambda: mock_service

        try:
            response = client.get(f"/api/decks/{deck_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["deck_id"] == deck_id
            assert data["status"] == "completed"
            assert data["slide_count"] == 1
        finally:
            # Clean up
            if get_deck_service in app.dependency_overrides:
                del app.dependency_overrides[get_deck_service]

    def test_modify_slide_api_contract(self, client, mock_deck_service_comprehensive):
        """Test slide modification API contract."""

        deck_id = str(uuid4())
        slide_order = 1

        request_data = {
            "modification_prompt": "Make this slide more colorful and engaging"
        }

        response = client.post(
            f"/api/decks/{deck_id}/slides/{slide_order}/modify",
            json=request_data,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["slide_order"] == slide_order
        assert data["status"] == "modifying"

        mock_deck_service_comprehensive.modify_slide.assert_called_once()

    def test_deck_export_api(self, client, mock_deck_service_comprehensive):
        """Test deck export API."""
        deck_id = str(uuid4())

        with patch("app.api.deck.render_deck_to_html") as mock_render:
            mock_render.return_value = "<html>Rendered deck</html>"

            response = client.get(f"/api/decks/{deck_id}/export?format=html")

            assert response.status_code == 200
            assert "text/html" in response.headers["content-type"]
            mock_render.assert_called_once()

    def test_list_decks_api(self, client, mock_deck_service_comprehensive):
        """Test deck listing API."""

        response = client.get("/api/decks?limit=10")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "deck_id" in data[0]

    def test_cancel_deck_api(self, client):
        """Test deck cancellation API."""
        from datetime import datetime

        from app.api.deck import get_deck_service
        from app.models.responses.deck import DeckStatusResponse

        deck_id = str(uuid4())

        # Create mock service that returns generating status
        mock_service = AsyncMock()
        mock_service.get_deck_status.side_effect = [
            DeckStatusResponse(
                deck_id=deck_id,
                status="generating",
                slide_count=0,
                created_at=datetime(2024, 1, 1),
            ),
            DeckStatusResponse(
                deck_id=deck_id,
                status="cancelled",
                slide_count=0,
                created_at=datetime(2024, 1, 1),
            ),
        ]

        # Override dependency
        app.dependency_overrides[get_deck_service] = lambda: mock_service

        try:
            with patch("app.api.deck.current_repo") as mock_repo_factory:
                mock_repo = AsyncMock()
                mock_repo_factory.return_value = mock_repo
                mock_repo.get_deck.return_value = {"status": "generating"}
                mock_repo.save_deck.return_value = None

                response = client.post(f"/api/decks/{deck_id}/cancel")

                assert response.status_code == 200
                data = response.json()
                assert data["deck_id"] == deck_id
                assert data["status"] == "cancelled"

                # Verify deck was marked as cancelled
                mock_repo.save_deck.assert_called()
        finally:
            # Clean up
            if get_deck_service in app.dependency_overrides:
                del app.dependency_overrides[get_deck_service]


class TestAPIErrorHandling:
    """Test API error handling separate from business logic."""

    def test_deck_not_found(self, client):
        """Test 404 handling."""
        non_existent_id = str(uuid4())

        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = None

            response = client.get(f"/api/decks/{non_existent_id}")
            assert response.status_code == 404

    def test_invalid_deck_id_format(self, client):
        """Test invalid UUID format handling."""
        response = client.get("/api/decks/invalid-uuid")
        assert response.status_code == 422

    def test_modify_non_completed_deck(self, client):
        """Test modification of non-completed deck."""
        from app.api.deck import get_deck_service

        deck_id = str(uuid4())

        # Create mock service that throws error
        mock_service = AsyncMock()
        mock_service.modify_slide.side_effect = ValueError(
            "Can only modify slides in completed or modifying decks. Current status: generating"
        )

        # Override dependency
        app.dependency_overrides[get_deck_service] = lambda: mock_service

        try:
            response = client.post(
                f"/api/decks/{deck_id}/slides/1/modify",
                json={"modification_prompt": "Test prompt"},
            )

            assert response.status_code == 400  # API converts ValueError to 400
        finally:
            # Clean up
            if get_deck_service in app.dependency_overrides:
                del app.dependency_overrides[get_deck_service]
