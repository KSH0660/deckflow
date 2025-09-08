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
def mock_generate_deck():
    """Mock the orchestration layer."""
    with patch("app.api.deck.generate_deck") as mock:
        mock.return_value = str(uuid4())
        yield mock


@pytest.fixture
def mock_modify_slide():
    """Mock the slide modification service."""
    with patch("app.api.deck.modify_slide") as mock:
        yield mock


class TestDeckAPIEndpoints:
    """Test API endpoints separately from business logic."""

    def test_create_deck_api_contract(self, client, mock_generate_deck):
        """Test deck creation API contract."""
        request_data = {
            "prompt": "Create a test presentation about API testing",
            "style": {"theme": "professional"},
            "files": None,
        }

        response = client.post("/api/v1/decks", json=request_data)

        assert response.status_code == 200
        response_data = response.json()
        assert "deck_id" in response_data
        assert "status" in response_data
        assert response_data["status"] == "generating"

        # Verify orchestration was called
        mock_generate_deck.assert_called_once()

    def test_create_deck_validation(self, client):
        """Test API request validation."""
        # Missing prompt
        response = client.post("/api/v1/decks", json={})
        assert response.status_code == 422

        # Prompt too short
        response = client.post("/api/v1/decks", json={"prompt": "Hi"})  # < 5 chars
        assert response.status_code == 422

        # Prompt too long
        long_prompt = "x" * 5001  # > 5000 chars
        response = client.post("/api/v1/decks", json={"prompt": long_prompt})
        assert response.status_code == 422

    def test_get_deck_status_api(self, client):
        """Test deck status retrieval API."""
        deck_id = str(uuid4())

        # Mock repository response
        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = {
                "id": deck_id,
                "status": "completed",
                "slides": [{"order": 1}],
                "created_at": "2024-01-01T00:00:00",
                "updated_at": None,
                "completed_at": "2024-01-01T00:05:00",
            }

            response = client.get(f"/api/v1/decks/{deck_id}")

            assert response.status_code == 200
            data = response.json()
            assert data["deck_id"] == deck_id
            assert data["status"] == "completed"
            assert data["slide_count"] == 1

    def test_modify_slide_api_contract(self, client, mock_modify_slide):
        """Test slide modification API contract."""
        deck_id = str(uuid4())
        slide_order = 1

        # Mock deck exists and is completed
        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = {
                "status": "completed",
                "slides": [{"order": 1}, {"order": 2}],
            }

            request_data = {
                "modification_prompt": "Make this slide more colorful and engaging"
            }

            response = client.post(
                f"/api/v1/decks/{deck_id}/slides/{slide_order}/modify",
                json=request_data,
            )

            assert response.status_code == 200
            data = response.json()
            assert data["deck_id"] == deck_id
            assert data["slide_order"] == slide_order
            assert data["status"] == "modifying"

            mock_modify_slide.assert_called_once()

    def test_deck_export_api(self, client):
        """Test deck export API."""
        deck_id = str(uuid4())

        # Mock deck exists
        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = {
                "id": deck_id,
                "deck_title": "Test Deck",
                "slides": [
                    {"order": 1, "content": {"html_content": "<div>Test slide</div>"}}
                ],
            }

            with patch("app.api.deck.render_deck_to_html") as mock_render:
                mock_render.return_value = "<html>Rendered deck</html>"

                response = client.get(f"/api/v1/decks/{deck_id}/export?format=html")

                assert response.status_code == 200
                assert "text/html" in response.headers["content-type"]
                mock_render.assert_called_once()

    def test_list_decks_api(self, client):
        """Test deck listing API."""
        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.list_all_decks.return_value = [
                {
                    "deck_id": str(uuid4()),
                    "title": "Test Deck 1",
                    "status": "completed",
                    "slide_count": 3,
                    "created_at": "2024-01-01T00:00:00",
                }
            ]

            response = client.get("/api/v1/decks?limit=10")

            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1
            assert "deck_id" in data[0]

    def test_cancel_deck_api(self, client):
        """Test deck cancellation API."""
        deck_id = str(uuid4())

        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = {
                "id": deck_id,
                "status": "generating",
                "slides": [],
                "created_at": "2024-01-01T00:00:00",
            }
            mock_repo.save_deck.return_value = None

            response = client.post(f"/api/v1/decks/{deck_id}/cancel")

            assert response.status_code == 200
            data = response.json()
            assert data["deck_id"] == deck_id
            assert data["status"] == "cancelled"

            # Verify deck was marked as cancelled
            mock_repo.save_deck.assert_called()


class TestAPIErrorHandling:
    """Test API error handling separate from business logic."""

    def test_deck_not_found(self, client):
        """Test 404 handling."""
        non_existent_id = str(uuid4())

        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = None

            response = client.get(f"/api/v1/decks/{non_existent_id}")
            assert response.status_code == 404

    def test_invalid_deck_id_format(self, client):
        """Test invalid UUID format handling."""
        response = client.get("/api/v1/decks/invalid-uuid")
        assert response.status_code == 422

    def test_modify_non_completed_deck(self, client):
        """Test modification of non-completed deck."""
        deck_id = str(uuid4())

        with patch("app.api.deck.current_repo") as mock_repo_factory:
            mock_repo = AsyncMock()
            mock_repo_factory.return_value = mock_repo
            mock_repo.get_deck.return_value = {
                "status": "generating",  # Not completed
                "slides": [],
            }

            response = client.post(
                f"/api/v1/decks/{deck_id}/slides/1/modify",
                json={"modification_prompt": "Test prompt"},
            )

            assert response.status_code == 400
            assert (
                "Can only modify slides in completed or modifying decks"
                in response.json()["detail"]
            )
