"""Read and validate the on-disk synthetic registry on every dependent request."""

import logging
from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from .models import Catalog

LOGGER = logging.getLogger(__name__)
UNAVAILABLE_DETAIL = "Local catalog unavailable or invalid; live AI readiness is not assessed."
MAX_CATALOG_BYTES = 1_048_576


class CatalogUnavailable(RuntimeError):
    """The local catalog dependency cannot safely be served."""


@dataclass(frozen=True)
class CatalogRegistry:
    path: Path

    def load(self) -> Catalog:
        try:
            raw_catalog = self.path.read_bytes()
            if len(raw_catalog) > MAX_CATALOG_BYTES:
                raise ValueError("Catalog exceeds the local registry size limit.")
            return Catalog.model_validate_json(raw_catalog)
        except (OSError, ValidationError, ValueError) as exc:
            # Do not log registry contents, which may contain a malformed local edit.
            LOGGER.error(
                "Local catalog dependency failed validation or reading (%s).",
                type(exc).__name__,
            )
            raise CatalogUnavailable(UNAVAILABLE_DETAIL) from exc
