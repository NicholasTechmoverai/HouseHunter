import pytest
from repositories.apartment import ApartmentRepository
from models.apartment import Apartment, ApartmentStatus, ApartmentType
from models.user import User
from core.cache import cache_manager

@pytest.fixture
def apartment_repo() -> ApartmentRepository:
    return ApartmentRepository()

@pytest.fixture
async def create_another_user() -> User:
    """Creates a secondary test user for referencing."""
    return await User.create(
        email="owner2@example.com",
        username="owner2",
        hashed_password="hashedpassword123",
        first_name="Second",
        last_name="Owner",
        is_active=True,
        is_verified=True,
        is_authenticated=True
    )

@pytest.fixture
async def sample_apartment_data(create_test_user: User) -> dict:
    return {
        "title": "Beautiful 2 Bedroom Apartment",
        "description": "A spacious and beautiful apartment close to the city center.",
        "price": 1200.0,
        "type": ApartmentType.APARTMENT,
        "bedrooms": 2,
        "bathrooms": 2,
        "area": 95.5,
        "address": "123 Main Street, Suite 4B",
        "city": "Nairobi",
        "amenities": ["wifi", "pool", "parking"],
        "images": [
            {"url": "https://example.com/img1.jpg", "caption": "Living room", "is_primary": True},
            {"url": "https://example.com/img2.jpg", "caption": "Kitchen", "is_primary": False},
            {"url": "https://example.com/img3.jpg", "caption": "Bedroom", "is_primary": False}
        ],
        "owner": create_test_user,
        "created_by": create_test_user,
        "status": ApartmentStatus.PENDING
    }

@pytest.mark.anyio
async def test_create_and_fetch_apartment(apartment_repo: ApartmentRepository, sample_apartment_data: dict):
    # Create apartment
    apt = await Apartment.create(**sample_apartment_data)
    assert apt.id is not None
    assert apt.title == sample_apartment_data["title"]
    
    # Fetch by ID
    fetched = await apartment_repo.get_by_id(str(apt.id))
    assert fetched is not None
    assert fetched.id == apt.id
    assert fetched.price == apt.price
    
    # Fetch by Owner
    owner_apts = await apartment_repo.get_by_owner(str(sample_apartment_data["owner"].id))
    assert len(owner_apts) == 1
    assert owner_apts[0].id == apt.id

@pytest.mark.anyio
async def test_publish_validation(apartment_repo: ApartmentRepository, create_test_user: User):
    # Create apartment with missing fields (no title, no images)
    apt = await Apartment.create(
        title="",
        description="",
        price=0,
        address="",
        city="",
        images=[],
        owner=create_test_user,
        created_by=create_test_user,
        status=ApartmentStatus.DRAFT
    )
    
    errors = await apartment_repo.validate_publish_requirements(apt)
    assert len(errors) > 0
    assert "Title is required" in errors
    assert "Description is required" in errors
    assert "Valid price is required" in errors
    assert "At least one image is required" in errors
    
    # Create a valid apartment
    apt_valid = await Apartment.create(
        title="Valid Apartment Title",
        description="A long enough description that meets validation rules.",
        price=1500.0,
        address="456 Oak Avenue",
        city="Mombasa",
        images=[{"url": "1.jpg"}, {"url": "2.jpg"}, {"url": "3.jpg"}],
        owner=create_test_user,
        created_by=create_test_user,
        status=ApartmentStatus.DRAFT
    )
    errors_valid = await apartment_repo.validate_publish_requirements(apt_valid)
    assert len(errors_valid) == 0

@pytest.mark.anyio
async def test_search_and_filter(apartment_repo: ApartmentRepository, create_test_user: User, sample_apartment_data: dict):
    # Setup test apartments
    # 1. Nairobi, 2 bedrooms, active
    apt1 = await Apartment.create(**sample_apartment_data)
    apt1.status = ApartmentStatus.ACTIVE
    await apt1.save()
    
    # 2. Mombasa, 1 bedroom, active
    sample2 = sample_apartment_data.copy()
    sample2["title"] = "Cozy Studio in Mombasa"
    sample2["city"] = "Mombasa"
    sample2["bedrooms"] = 1
    sample2["price"] = 800.0
    sample2["type"] = ApartmentType.STUDIO
    apt2 = await Apartment.create(**sample2)
    apt2.status = ApartmentStatus.ACTIVE
    await apt2.save()

    # Test search by city
    apts, total = await apartment_repo.search_apartments(city="Nairobi", status="active")
    assert total == 1
    assert apts[0].id == apt1.id
    
    # Test search by price range
    apts, total = await apartment_repo.search_apartments(min_price=1000, max_price=2000, status="active")
    assert total == 1
    assert apts[0].id == apt1.id

    # Test text search (uses icontains)
    search_results = await apartment_repo.text_search(query_text="cozy")
    assert len(search_results) == 1
    assert search_results[0].id == apt2.id

@pytest.mark.anyio
async def test_get_stats(apartment_repo: ApartmentRepository, create_test_user: User, sample_apartment_data: dict):
    # Initially no stats
    stats_empty = await apartment_repo.get_stats()
    assert stats_empty["total"] == 0
    
    # Create active apartment
    sample1 = sample_apartment_data.copy()
    sample1["status"] = ApartmentStatus.ACTIVE
    await Apartment.create(**sample1)
    
    # Create pending apartment
    await Apartment.create(**sample_apartment_data)
    
    # Re-fetch stats (we mock or clear cache since get_stats caches results)
    await cache_manager.delete("apartment_stats")
    stats = await apartment_repo.get_stats()
    # Note: since get_stats uses caching, let's verify cache works!
    assert stats["total"] == 2
    assert stats["active"] == 1
    assert stats["pending"] == 1

@pytest.mark.anyio
async def test_to_schemas(apartment_repo: ApartmentRepository, create_test_user: User, sample_apartment_data: dict):
    apt = await Apartment.create(**sample_apartment_data)
    
    # Test summary schema conversion
    summary = await apartment_repo.to_summary_schema(apt)
    assert summary.id == str(apt.id)
    assert summary.title == apt.title
    assert summary.price == float(apt.price)
    
    # Test detail schema conversion
    detail = await apartment_repo.to_schema(apt)
    assert detail.id == str(apt.id)
    assert detail.owner.username == create_test_user.username
    assert len(detail.images) == 3
    assert detail.images[0].url == "https://example.com/img1.jpg"
