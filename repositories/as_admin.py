# repositories/admin_repository.py
from typing import List, Optional

from tortoise.expressions import Q
from core.logger import setup_logger

from models.user import User
from models.for_rent import RentalComplex
from repositories.user import UserRepository
from repositories.rentals import RentalRepository, resolve_image_url

logger = setup_logger(__name__)


def get_asadmin_repo():
    return AsAdminRepository()


class AsAdminRepository(UserRepository, RentalRepository):
    def __init__(self):
        self.users = User
        self.rentals = RentalComplex

    # ======================
    # USER READ OPERATIONS
    # ======================

    async def get_all_users(self, offset: int = 0, limit: int = 20) -> List[User]:
        try:
            return await self.users.all().offset(offset).limit(limit)
        except Exception as e:
            logger.exception("Failed to fetch all users")
            raise

    async def get_unverified_users(
        self, offset: int = 0, limit: int = 20
    ) -> List[User]:
        try:
            return (
                await self.users.filter(is_verified=False).offset(offset).limit(limit)
            )
        except Exception as e:
            logger.exception("Failed to fetch unverified users")
            raise

    async def get_inactive_users(self, offset: int = 0, limit: int = 20) -> List[User]:
        try:
            return await self.users.filter(is_active=False).offset(offset).limit(limit)
        except Exception as e:
            logger.exception("Failed to fetch inactive users")
            raise

    async def search_users(
        self, query: Optional[str] = None, offset: int = 0, limit: int = 20
    ) -> List[User]:
        try:
            qs = self.users.all()

            if query:
                qs = qs.filter(
                    Q(email__icontains=query)
                    | Q(username__icontains=query)
                    | Q(full_name__icontains=query)
                )

            return await qs.offset(offset).limit(limit)

        except Exception as e:
            logger.exception(
                "Failed to search users",
                extra={"query": query, "offset": offset, "limit": limit},
            )
            raise

    # ======================
    # RENTAL READ OPERATIONS
    # ======================

    async def get_all_rentals(self, offset: int = 0, limit: int = 20):
        try:
            rentals = (
                await self.rentals.all()
                .offset(offset)
                .limit(limit)
                .prefetch_related(
                    "rules",
                    "amenities",
                    "pricing__fees",
                    "gallery",
                    "publisher",
                    "managers",
                )
            )

            return [self.quick_rental_view(r) for r in rentals]

        except Exception as e:
            logger.exception("Failed to fetch all rentals")
            raise

    async def get_unverified_rentals(
        self, offset: int = 0, limit: int = 20
    ) -> List[RentalComplex]:
        try:
            return (
                await self.rentals.filter(is_verified=False)
                .offset(offset)
                .limit(limit)
                .prefetch_related(
                    "rules",
                    "amenities",
                    "pricing__fees",
                    "gallery",
                    "publisher",
                    "managers",
                )
            )
        except Exception as e:
            logger.exception("Failed to fetch unverified rentals")
            raise

    async def get_inactive_rentals(
        self, offset: int = 0, limit: int = 20
    ) -> List[RentalComplex]:
        try:
            return (
                await self.rentals.filter(is_active=False)
                .offset(offset)
                .limit(limit)
                .prefetch_related(
                    "rules",
                    "amenities",
                    "pricing__fees",
                    "gallery",
                    "publisher",
                    "managers",
                )
            )
        except Exception as e:
            logger.exception("Failed to fetch inactive rentals")
            raise

    # ======================
    # SERIALIZER
    # ======================

    def quick_rental_view(self, rental: RentalComplex) -> dict:
        try:
            return {
                "public_id": rental.public_id,
                "status": (
                    rental.status.value
                    if hasattr(rental.status, "value")
                    else rental.status
                ),
                "created_at": (
                    rental.created_at.isoformat() if rental.created_at else None
                ),
                "title": rental.title,
                "slug": rental.slug,
                "theme_color": rental.theme_color,
                "category": rental.category,
                "description": rental.description,
                "profile_picture": resolve_image_url(rental.profile_picture),
                "price": (
                    float(rental.pricing.rent)
                    if rental.pricing and rental.pricing.rent
                    else None
                ),
                "deposit": (
                    float(rental.pricing.deposit_amount)
                    if rental.pricing and rental.pricing.deposit_amount
                    else None
                ),
                "location": (
                    f"{rental.city}, {rental.state}"
                    if rental.city and rental.state
                    else rental.address
                ),
                "contact": getattr(rental, "contact", None),
                "available": rental.is_available,
                "rating": getattr(rental, "rating", 0),
                "publisher": {
                    "public_id": rental.publisher.public_id,
                    "display_name": rental.publisher.display_name,
                    "profile_picture": rental.publisher.profile_picture,
                },
            }

        except Exception:
            logger.exception(
                "Failed to serialize rental",
                extra={"rental_id": getattr(rental, "id", None)},
            )
            raise
