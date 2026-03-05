from enum import StrEnum


class SearchType(StrEnum):
    RU = "SEARCH_TYPE_RU"
    TR = "SEARCH_TYPE_TR"
    COM = "SEARCH_TYPE_COM"
    KK = "SEARCH_TYPE_KK"
    BE = "SEARCH_TYPE_BE"
    UZ = "SEARCH_TYPE_UZ"


class FamilyMode(StrEnum):
    NONE = "FAMILY_MODE_NONE"
    MODERATE = "FAMILY_MODE_MODERATE"
    STRICT = "FAMILY_MODE_STRICT"


class FixTypoMode(StrEnum):
    ON = "FIX_TYPO_MODE_ON"
    OFF = "FIX_TYPO_MODE_OFF"


class SortMode(StrEnum):
    BY_RELEVANCE = "SORT_MODE_BY_RELEVANCE"
    BY_TIME = "SORT_MODE_BY_TIME"


class SortOrder(StrEnum):
    ASC = "SORT_ORDER_ASC"
    DESC = "SORT_ORDER_DESC"


class GroupMode(StrEnum):
    FLAT = "GROUP_MODE_FLAT"
    DEEP = "GROUP_MODE_DEEP"


class L10n(StrEnum):
    RU = "L10N_RU"
    UK = "L10N_UK"
    BE = "L10N_BE"
    KK = "L10N_KK"
    TR = "L10N_TR"
    EN = "L10N_EN"


class ResponseFormat(StrEnum):
    XML = "FORMAT_XML"
    HTML = "FORMAT_HTML"


class ImageFormat(StrEnum):
    JPEG = "IMAGE_FORMAT_JPEG"
    GIF = "IMAGE_FORMAT_GIF"
    PNG = "IMAGE_FORMAT_PNG"


class ImageSize(StrEnum):
    ENORMOUS = "IMAGE_SIZE_ENORMOUS"
    LARGE = "IMAGE_SIZE_LARGE"
    MEDIUM = "IMAGE_SIZE_MEDIUM"
    SMALL = "IMAGE_SIZE_SMALL"
    TINY = "IMAGE_SIZE_TINY"
    WALLPAPER = "IMAGE_SIZE_WALLPAPER"


class ImageOrientation(StrEnum):
    VERTICAL = "IMAGE_ORIENTATION_VERTICAL"
    HORIZONTAL = "IMAGE_ORIENTATION_HORIZONTAL"
    SQUARE = "IMAGE_ORIENTATION_SQUARE"


class ImageColor(StrEnum):
    COLOR = "IMAGE_COLOR_COLOR"
    GRAYSCALE = "IMAGE_COLOR_GRAYSCALE"
    RED = "IMAGE_COLOR_RED"
    ORANGE = "IMAGE_COLOR_ORANGE"
    YELLOW = "IMAGE_COLOR_YELLOW"
    GREEN = "IMAGE_COLOR_GREEN"
    CYAN = "IMAGE_COLOR_CYAN"
    BLUE = "IMAGE_COLOR_BLUE"
    VIOLET = "IMAGE_COLOR_VIOLET"
    WHITE = "IMAGE_COLOR_WHITE"
    BLACK = "IMAGE_COLOR_BLACK"


class MessageRole(StrEnum):
    USER = "ROLE_USER"
    ASSISTANT = "ROLE_ASSISTANT"


class ContentFormat(StrEnum):
    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
