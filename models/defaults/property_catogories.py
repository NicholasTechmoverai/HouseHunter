
from enum import IntEnum


class PropertyCategory(IntEnum):
    # Residential single units / rooms
    SINGLE_ROOM = 1
    DOUBLE_ROOM = 2
    BEDSITTER = 3
    STUDIO = 4

    # Residential houses by bedrooms
    ONE_BEDROOM = 10
    TWO_BEDROOM = 11
    THREE_BEDROOM = 12
    FOUR_BEDROOM = 13
    FIVE_BEDROOM = 14

    # Residential full units
    APARTMENT = 20
    MAISONETTE = 21
    BUNGALOW = 22
    MANSION = 23
    VILLA = 24
    PENTHOUSE = 25

    # Shared / hospitality / short stay
    HOSTEL_ROOM = 30
    SHARED_ROOM = 31
    AIRBNB_ROOM = 32
    GUEST_HOUSE = 33
    SERVICED_APARTMENT = 34
    HOTEL_ROOM = 35
    LODGE = 36

    # Commercial property
    SHOP = 40
    SUPERMARKET_SPACE = 41
    MALL_UNIT = 42
    OFFICE_SPACE = 43
    WAREHOUSE = 44
    INDUSTRIAL_SPACE = 45
    RESTAURANT_SPACE = 46
    SHOWROOM = 47