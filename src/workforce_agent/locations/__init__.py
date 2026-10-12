from __future__ import annotations

import json
from importlib.resources import files

from pydantic import Field

from workforce_agent.schemas import Site
from workforce_agent.schemas.common import StrictModel


class LocationProfile(StrictModel):
    location_id: str = Field(..., min_length=1)
    display_name: str = Field(..., min_length=1)
    country: str = Field(..., min_length=2, max_length=2)
    sites: list[Site] = Field(..., min_length=1)


def _iter_location_payloads() -> list[dict]:
    root = files("workforce_agent.locations")
    payloads: list[dict] = []
    for item in root.iterdir():
        if item.name.endswith(".json"):
            payloads.append(json.loads(item.read_text(encoding="utf-8")))
    return payloads


def list_location_ids() -> list[str]:
    return sorted(payload["location_id"] for payload in _iter_location_payloads())


def load_location(location_id: str) -> LocationProfile:
    for payload in _iter_location_payloads():
        if payload.get("location_id") == location_id:
            return LocationProfile.model_validate(payload)
    known = ", ".join(list_location_ids()) or "(none)"
    raise KeyError(f"unknown location_id {location_id!r}; available: {known}")


def load_site(site_id: str, location_id: str | None = None) -> Site:
    profiles = (
        [load_location(location_id)]
        if location_id
        else [load_location(item) for item in list_location_ids()]
    )
    for profile in profiles:
        for site in profile.sites:
            if site.site_id == site_id:
                return site
    raise KeyError(f"unknown site_id {site_id!r}")
