import pytest
from repositories.user import UserRepository
from models.user import User

@pytest.fixture
def user_repo() -> UserRepository:
    return UserRepository()

@pytest.mark.anyio
async def test_user_repo_create_and_find(user_repo: UserRepository, sample_user_data: dict):
    # Ensure user does not exist
    assert await user_repo.exists(sample_user_data["email"]) is False
    
    # Create user
    user = await User.create(
        email=sample_user_data["email"],
        username=sample_user_data["username"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        status=1
    )
    
    # Verify save generated fields automatically (public_id, username)
    assert user.public_id is not None
    assert user.public_id.startswith("USR")
    
    # Check exists with different identifiers
    assert await user_repo.exists(user.email) is True
    assert await user_repo.exists(user.username) is True
    assert await user_repo.exists(str(user.id)) is True
    assert await user_repo.exists(user.public_id) is True
    
    # Find user
    found_by_email = await user_repo.get_by_email(user.email)
    assert found_by_email is not None
    assert found_by_email.id == user.id
    
    found_by_id = await user_repo.get_by_id(str(user.id))
    assert found_by_id is not None
    assert found_by_id.email == user.email

@pytest.mark.anyio
async def test_user_repo_register(user_repo: UserRepository, sample_user_data: dict):
    # Register user
    result = await user_repo.register(
        email=sample_user_data["email"],
        first_name=sample_user_data["first_name"],
        last_name=sample_user_data["last_name"],
        password=sample_user_data["password"],
        username=sample_user_data["username"],
        phone_number=sample_user_data["phone_number"]
    )
    
    assert result["success"] is True
    assert result["user"]["email"] == sample_user_data["email"]
    
    # Test duplicate registration
    dup_result = await user_repo.register(
        email=sample_user_data["email"],
        first_name="Another",
        password="Password123!"
    )
    assert dup_result["success"] is False
    assert "Email already registered" in dup_result["message"]

@pytest.mark.anyio
async def test_username_availability(user_repo: UserRepository, create_test_user: User):
    # Reserved usernames
    avail_check = await user_repo.is_username_available("admin")
    assert avail_check["available"] is False
    assert avail_check["reason"] == "reserved"
    
    # Invalid format
    avail_check = await user_repo.is_username_available("a")
    assert avail_check["available"] is False
    assert avail_check["reason"] == "invalid_format"
    
    # Taken username
    avail_check = await user_repo.is_username_available(create_test_user.username)
    assert avail_check["available"] is False
    assert avail_check["reason"] == "taken"
    
    # Available username
    avail_check = await user_repo.is_username_available("uniqueusername123")
    assert avail_check["available"] is True

@pytest.mark.anyio
async def test_password_lifecycle(user_repo: UserRepository, create_test_user: User):
    # Verify current password check
    with pytest.raises(ValueError) as exc:
        await user_repo.change_password(
            user=create_test_user,
            current_password="WrongPassword123!",
            new_password="NewSecurePassword123!"
        )
    assert "Current password is incorrect" in str(exc.value)
    
    # Successfully change password
    updated_user = await user_repo.change_password(
        user=create_test_user,
        current_password="Password123!",
        new_password="NewSecurePassword123!"
    )
    assert updated_user.password_changed_count > 0
    assert updated_user.check_password("NewSecurePassword123!") is True
