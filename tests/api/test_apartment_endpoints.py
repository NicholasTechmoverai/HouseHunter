import pytest
from httpx import AsyncClient
from models.user import User
from models.apartment import Apartment, ApartmentStatus, ApartmentType

@pytest.fixture
async def valid_apartment_payload() -> dict:
    return {
        "title": "Stunning Luxury Loft in Westlands",
        "description": "This is a premium and beautiful loft in Westlands, Nairobi. Close to amenities and fully furnished.",
        "price": 2500.0,
        "type": ApartmentType.LOFT.value,
        "bedrooms": 3,
        "bathrooms": 2,
        "area": 120.0,
        "address": "456 Westlands Road, Nairobi",
        "city": "Nairobi",
        "amenities": ["wifi", "gym", "elevator", "parking"],
        "latitude": -1.265,
        "longitude": 36.808
    }

@pytest.mark.anyio
async def test_create_apartment_unauthenticated(client: AsyncClient, valid_apartment_payload: dict):
    response = await client.post("/api/v1/apartments/", json=valid_apartment_payload)
    assert response.status_code == 401

@pytest.mark.anyio
async def test_create_apartment_success(client: AsyncClient, auth_headers: dict, valid_apartment_payload: dict):
    response = await client.post("/api/v1/apartments/", json=valid_apartment_payload, headers=auth_headers)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == valid_apartment_payload["title"]
    assert data["status"] == ApartmentStatus.PENDING.value
    assert "owner" in data

@pytest.mark.anyio
async def test_list_apartments_success(client: AsyncClient, auth_headers: dict, create_test_user: User, valid_apartment_payload: dict):
    # Create an active apartment directly in DB
    apt = await Apartment.create(
        title=valid_apartment_payload["title"],
        description=valid_apartment_payload["description"],
        price=valid_apartment_payload["price"],
        type=valid_apartment_payload["type"],
        bedrooms=valid_apartment_payload["bedrooms"],
        bathrooms=valid_apartment_payload["bathrooms"],
        area=valid_apartment_payload["area"],
        address=valid_apartment_payload["address"],
        city=valid_apartment_payload["city"],
        amenities=valid_apartment_payload["amenities"],
        images=[{"url": "https://example.com/img1.jpg", "caption": "Lobby"}],
        owner=create_test_user,
        created_by=create_test_user,
        status=ApartmentStatus.ACTIVE
    )
    
    response = await client.get("/api/v1/apartments/", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "apartments" in data
    assert len(data["apartments"]) >= 1
    assert data["apartments"][0]["title"] == valid_apartment_payload["title"]

@pytest.mark.anyio
async def test_publish_apartment_success(client: AsyncClient, auth_headers: dict, create_test_user: User, valid_apartment_payload: dict):
    # Create an apartment with required 3 images so it passes validation rules
    apt = await Apartment.create(
        title=valid_apartment_payload["title"],
        description=valid_apartment_payload["description"],
        price=valid_apartment_payload["price"],
        type=valid_apartment_payload["type"],
        bedrooms=valid_apartment_payload["bedrooms"],
        bathrooms=valid_apartment_payload["bathrooms"],
        area=valid_apartment_payload["area"],
        address=valid_apartment_payload["address"],
        city=valid_apartment_payload["city"],
        amenities=valid_apartment_payload["amenities"],
        images=[
            {"url": "1.jpg"},
            {"url": "2.jpg"},
            {"url": "3.jpg"}
        ],
        owner=create_test_user,
        created_by=create_test_user,
        status=ApartmentStatus.DRAFT
    )
    
    # Publish it
    response = await client.post(
        f"/api/v1/apartments/{apt.id}/publish",
        json={"publish": True},
        headers=auth_headers
    )
    assert response.status_code == 200
    assert response.json()["status"] == ApartmentStatus.ACTIVE.value
