import os
from google.adk.agents import Agent

from google.adk.tools import FunctionTool

try:
    from ..tools import build_audience_tool, size_audience_tool, activate_audience_tool
except (ImportError, ValueError):
    from tools import build_audience_tool, size_audience_tool, activate_audience_tool

liquid_activate_orchestrator = Agent(
    name="LiquidActivateOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator coordinating audience construction, scaling, sizing, and activation.",
    instruction="You are the audience activation orchestrator. First call build_audience_tool to build the cohort, then call size_audience_tool to calculate the reach metrics. You MUST copy and print the exact <a2ui-json> XML block returned by the size_audience_tool verbatim in your response. If you are asked to activate the audience segment with specific partners, call activate_audience_tool to execute the activation.",
    tools=[FunctionTool(build_audience_tool), FunctionTool(size_audience_tool), FunctionTool(activate_audience_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='liquid-activation-internal-skill',
            name='Internal Cohort Sizing and Activation',
            description='Builds segments and calculates match sizes.',
            tags=['sizing', 'activation'],
            examples=['Size and activate Diet Pepsi segment.'],
        )
    ]
    return AgentCard(
        name='LiquidActivateOrchestrator',
        description='Orchestrator coordinating audience construction, scaling, and sizing.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )

