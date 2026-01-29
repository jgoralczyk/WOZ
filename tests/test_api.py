"""
API endpoint tests for WOZ application.
"""

import pytest


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_check(self, client):
        """Test main health endpoint."""
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "WOZ API"

    @pytest.mark.asyncio
    async def test_health_db(self, client):
        """Test database health endpoint."""
        response = await client.get("/health/db")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestWnioskiEndpoints:
    """Tests for wnioski CRUD endpoints."""

    @pytest.mark.asyncio
    async def test_create_wniosek(self, client, sample_wniosek_data):
        """Test creating a new wniosek."""
        response = await client.post("/wnioski/", json=sample_wniosek_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["id"] == 1

    @pytest.mark.asyncio
    async def test_get_wnioski_empty(self, client):
        """Test getting wnioski when empty."""
        response = await client.get("/wnioski/?user=test&role=payroll")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_get_wnioski_after_create(self, client, sample_wniosek_data):
        """Test getting wnioski after creating one."""
        # Create wniosek
        await client.post("/wnioski/", json=sample_wniosek_data)
        
        # Get wnioski
        response = await client.get("/wnioski/?user=test&role=payroll")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == sample_wniosek_data["title"]

    @pytest.mark.asyncio
    async def test_get_wniosek_by_id(self, client, sample_wniosek_data):
        """Test getting a specific wniosek by ID."""
        # Create wniosek
        create_response = await client.post("/wnioski/", json=sample_wniosek_data)
        wniosek_id = create_response.json()["id"]
        
        # Get by ID
        response = await client.get(f"/wnioski/{wniosek_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == wniosek_id
        assert data["title"] == sample_wniosek_data["title"]

    @pytest.mark.asyncio
    async def test_get_wniosek_not_found(self, client):
        """Test getting a non-existent wniosek."""
        response = await client.get("/wnioski/999")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_update_wniosek_status(self, client, sample_wniosek_data):
        """Test updating wniosek status."""
        # Create wniosek
        create_response = await client.post("/wnioski/", json=sample_wniosek_data)
        wniosek_id = create_response.json()["id"]
        
        # Update status
        response = await client.put(
            f"/wnioski/{wniosek_id}/status?new_status=Completed"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["new_status"] == "Completed"

    @pytest.mark.asyncio
    async def test_update_wniosek_invalid_status(self, client, sample_wniosek_data):
        """Test updating wniosek with invalid status."""
        # Create wniosek
        create_response = await client.post("/wnioski/", json=sample_wniosek_data)
        wniosek_id = create_response.json()["id"]
        
        # Update with invalid status
        response = await client.put(
            f"/wnioski/{wniosek_id}/status?new_status=InvalidStatus"
        )
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_wniosek(self, client, sample_wniosek_data):
        """Test deleting a wniosek."""
        # Create wniosek
        create_response = await client.post("/wnioski/", json=sample_wniosek_data)
        wniosek_id = create_response.json()["id"]
        
        # Delete
        response = await client.delete(f"/wnioski/{wniosek_id}")
        assert response.status_code == 200
        
        # Verify deleted
        get_response = await client.get(f"/wnioski/{wniosek_id}")
        assert get_response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_wnioski_requires_user(self, client):
        """Test that user parameter is required."""
        response = await client.get("/wnioski/")
        assert response.status_code == 422  # Validation error


class TestStatsEndpoint:
    """Tests for statistics endpoint."""

    @pytest.mark.asyncio
    async def test_get_stats_empty(self, client):
        """Test getting stats when no wnioski exist."""
        response = await client.get("/stats/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_wnioski"] == 0
        assert data["total_payoff"] == 0

    @pytest.mark.asyncio
    async def test_get_stats_with_data(self, client, sample_wniosek_data):
        """Test getting stats after creating wnioski."""
        # Create two wnioski
        await client.post("/wnioski/", json=sample_wniosek_data)
        await client.post("/wnioski/", json=sample_wniosek_data)
        
        # Get stats
        response = await client.get("/stats/")
        assert response.status_code == 200
        data = response.json()
        assert data["total_wnioski"] == 2
        assert data["total_payoff"] == 3000.0  # 1500 * 2
