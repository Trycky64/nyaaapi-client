"""Constants describing the public Nyaa-API service."""

from enum import StrEnum

DEFAULT_BASE_URL = "https://nyaaapi.onrender.com"
DEFAULT_TIMEOUT = 30.0


class SortOrder(StrEnum):
    """Order values explicitly described by the OpenAPI parameter documentation."""

    ASC = "asc"
    DESC = "desc"
