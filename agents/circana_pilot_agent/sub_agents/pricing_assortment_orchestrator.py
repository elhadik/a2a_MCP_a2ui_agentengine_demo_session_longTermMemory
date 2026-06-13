import os
from google.adk.agents import Agent

from google.adk.tools import FunctionTool

try:
    from ..tools import pricing_opportunities_tool
except (ImportError, ValueError):
    from tools import pricing_opportunities_tool

pricing_assortment_orchestrator = Agent(
    name="PricingAssortmentOrchestrator",
    model=os.environ.get("GOOGLE_GENAI_MODEL", "gemini-2.5-flash"),
    description="Orchestrator that analyzes price increases and shopper attrition tables.",
    instruction="You are the pricing orchestrator. Call your pricing_opportunities_tool to identify buyer attrition products. You MUST copy and print the exact <a2ui-json> XML block returned by the tool verbatim at the end of your response without altering any character.",
    tools=[FunctionTool(pricing_opportunities_tool)]
)

def get_agent_card(host: str, port: int) -> "AgentCard":
    from a2a.types import AgentCard, AgentSkill, AgentCapabilities, TransportProtocol
    skills = [
        AgentSkill(
            id='pricing-assortment-internal-skill',
            name='Internal Pricing Assortment Analysis',
            description='Identifies pricing opportunities and shopper attrition.',
            tags=['pricing'],
            examples=['Identify products with high attrition.'],
        )
    ]
    return AgentCard(
        name='PricingAssortmentOrchestrator',
        description='Orchestrator that analyzes price increases and shopper attrition tables.',
        url=f'http://{host}:{port}/',
        version='1.0.0',
        default_input_modes=['text'],
        default_output_modes=['text'],
        capabilities=AgentCapabilities(streaming=False),
        skills=skills,
        preferred_transport=TransportProtocol.http_json,
    )

