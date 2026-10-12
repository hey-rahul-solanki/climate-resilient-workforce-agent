class WeatherError(Exception):
    """Base error for weather ingestion."""


class WeatherUnavailableError(WeatherError):
    """Provider could not be reached or returned an HTTP error."""


class WeatherIncompleteError(WeatherError):
    """Forecast payload is missing required series or hours."""
