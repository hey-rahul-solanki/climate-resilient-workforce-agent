"""
Factory classes for creating services based on configuration.

These factories allow switching between static mode (no external dependencies)
and dynamic mode (with external APIs) via environment variables.
"""

from workforce_agent.config import settings


class WeatherClientFactory:
    """Factory to create weather client based on configuration"""

    @staticmethod
    def get_client():
        """Get weather client based on WORKFORCE_WEATHER_SOURCE setting"""
        from workforce_agent.weather.client import OpenMeteoClient, FixtureWeatherClient

        if settings.weather_source == "fixture":
            return FixtureWeatherClient(settings.fixture_path)
        elif settings.weather_source == "open-meteo":
            return OpenMeteoClient(settings.open_meteo_base_url)
        elif settings.weather_source == "meteor":
            # Meteor client to be implemented when needed
            raise NotImplementedError("Meteor client not yet implemented")
        else:
            raise ValueError(f"Unknown weather source: {settings.weather_source}")


class LocationServiceFactory:
    """Factory to create location service based on configuration"""

    @staticmethod
    def get_service():
        """Get location service based on WORKFORCE_LOCATION_SOURCE setting"""
        from workforce_agent.ai.location_service import StaticLocationService, OSMLocationService

        if settings.location_source == "static":
            return StaticLocationService()
        elif settings.location_source == "osm":
            return OSMLocationService()
        else:
            raise ValueError(f"Unknown location source: {settings.location_source}")


class AIServiceFactory:
    """Factory to create AI service based on configuration"""

    @staticmethod
    def get_service():
        """Get AI service based on WORKFORCE_AI_SOURCE setting"""
        from workforce_agent.ai.ai_service import RuleBasedAIService

        if settings.ai_source == "rule_based":
            return RuleBasedAIService()
        elif settings.ai_source == "gemini":
            # Gemini service to be implemented when needed
            raise NotImplementedError("Gemini AI service not yet implemented")
        else:
            raise ValueError(f"Unknown AI source: {settings.ai_source}")
