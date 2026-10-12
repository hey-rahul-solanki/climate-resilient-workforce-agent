from __future__ import annotations

import argparse
import json

from workforce_agent.config import get_settings
from workforce_agent.locations import load_location, load_site
from workforce_agent.weather.client import build_weather_client


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Fetch a site weather forecast.")
    parser.add_argument("--location-id", default=None, help="Location catalog id (default from settings).")
    parser.add_argument("--site-id", default=None, help="Site id within the location catalog.")
    parser.add_argument("--forecast-days", type=int, default=3)
    args = parser.parse_args(argv)

    settings = get_settings()
    location_id = args.location_id or settings.default_location_id
    location = load_location(location_id)
    site = load_site(args.site_id, location_id) if args.site_id else location.sites[0]
    client = build_weather_client(settings)
    forecast = client.get_forecast(site, forecast_days=args.forecast_days)
    print(json.dumps(forecast.model_dump(mode="json"), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
