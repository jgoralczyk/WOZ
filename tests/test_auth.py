"""
Authentication endpoint tests for WOZ application.
"""

import pytest


class TestAuthEndpoints:
    """Tests for authentication endpoints."""

    @pytest.mark.asyncio
    async def test_register_user(self, client, sample_user_data):
        """Test user registration."""
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == sample_user_data["email"]
        assert data["user"]["full_name"] == sample_user_data["full_name"]
        assert data["user"]["role"] == "user"

    @pytest.mark.asyncio
    async def test_register_duplicate_email(self, client, sample_user_data):
        """Test registration with duplicate email."""
        # First registration
        await client.post("/auth/register", json=sample_user_data)
        
        # Second registration with same email
        response = await client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "już istnieje" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_register_weak_password(self, client):
        """Test registration with weak password."""
        response = await client.post("/auth/register", json={
            "email": "test@example.com",
            "password": "short",  # Less than 8 characters
            "full_name": "Test User"
        })
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_login_success(self, client, sample_user_data):
        """Test successful login."""
        # Register first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login
        response = await client.post("/auth/login", json={
            "email": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, client, sample_user_data):
        """Test login with wrong password."""
        # Register first
        await client.post("/auth/register", json=sample_user_data)
        
        # Login with wrong password
        response = await client.post("/auth/login", json={
            "email": sample_user_data["email"],
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, client):
        """Test login with non-existent user."""
        response = await client.post("/auth/login", json={
            "email": "nonexistent@example.com",
            "password": "somepassword"
        })
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_authenticated(self, client, sample_user_data):
        """Test getting current user when authenticated."""
        # Register and get token
        register_response = await client.post("/auth/register", json=sample_user_data)
        token = register_response.json()["access_token"]
        
        # Get current user
        response = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == sample_user_data["email"]

    @pytest.mark.asyncio
    async def test_get_me_unauthenticated(self, client):
        """Test getting current user without authentication."""
        response = await client.get("/auth/me")
        assert response.status_code == 403  # No credentials

    @pytest.mark.asyncio
    async def test_get_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_token(self, client, sample_user_data):
        """Test refreshing access token."""
        # Register and get tokens
        register_response = await client.post("/auth/register", json=sample_user_data)
        refresh_token = register_response.json()["refresh_token"]
        
        # Refresh token
        response = await client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    @pytest.mark.asyncio
    async def test_refresh_with_invalid_token(self, client):
        """Test refreshing with invalid token."""
        response = await client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401
