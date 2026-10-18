"""Shared construction for the agent service used by HTTP and MCP adapters."""
from workforce_agent.agent import AgentService
from workforce_agent.approval import ApprovalStore
from workforce_agent.config import get_settings
from workforce_agent.weather.client import build_weather_client


class ConfiguredWeatherClient:
    """Resolve weather configuration at request time."""
    def get_forecast(self, site, window):
        return build_weather_client(get_settings()).get_forecast(site, window)


def build_agent_service():
    settings = get_settings()
    reasoning = None
    if settings.reasoning_provider == 'vertex':
        from workforce_agent.reasoning import ReasoningService, VertexADKProvider
        reasoning = ReasoningService(
            VertexADKProvider(settings),
            input_rate=settings.model_input_usd_per_million,
            output_rate=settings.model_output_usd_per_million,
        )
    return AgentService(
        approval_store=ApprovalStore(settings.approval_db_path),
        reasoning=reasoning,
        weather_client=ConfiguredWeatherClient(),
    )


# Each runtime process owns its session state and shares configured durable stores.
service = build_agent_service()
