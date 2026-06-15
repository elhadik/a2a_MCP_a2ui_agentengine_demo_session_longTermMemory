import os
from google.adk.agents import Agent
from google.adk.tools import FunctionTool

try:
    from ..tools import send_message_tool, activate_audience_tool, profile_audience_tool
except (ImportError, ValueError):
    from tools import send_message_tool, activate_audience_tool, profile_audience_tool

ROLE_DESCRIPTION = (
    "You are the Circana Liquid Activate Orchestrator. Your job is to coordinate audience construction, scaling, and sizing. "
    "To handle user queries, execute this sequential plan using your send_message_tool:\n"
    "1. Delegate to 'SemanticLayerAgent' with the user request to resolve the target product entity (e.g. 'Diet Pepsi 12pk') from conversation memory.\n"
    "2. Delegate to 'AudienceBuildAgent' with the resolved product entity to isolate and build the shopper cohort.\n"
    "3. Delegate to 'AudienceScaleAgent' with the audience ID returned by the AudienceBuildAgent to perform lookalike scaling.\n"
    "4. Delegate to 'AudienceSizeAgent' with the scaled audience ID to compile the reach metrics and obtain the sizing dashboard.\n"
    "5. Print the exact sizing metrics summary and print the <a2ui-json> XML block verbatim in your final response.\n\n"
    "If you are explicitly asked to activate the segment with partners, call activate_audience_tool directly.\n"
    "If you are asked to profile or analyze demographic distributions, call profile_audience_tool."
)

liquid_activate_orchestrator = Agent(
    name="LiquidActivateOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator coordinating audience construction, scaling, sizing, profiling, and activation.",
    instruction=ROLE_DESCRIPTION,
    tools=[FunctionTool(send_message_tool), FunctionTool(activate_audience_tool), FunctionTool(profile_audience_tool)]
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
