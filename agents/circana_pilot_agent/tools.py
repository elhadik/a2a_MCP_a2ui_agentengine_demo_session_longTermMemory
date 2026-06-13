import json
import logging

try:
    from .components import get_product_table_a2ui, get_sizing_dashboard_a2ui
except ImportError:
    from components import get_product_table_a2ui, get_sizing_dashboard_a2ui

logger = logging.getLogger(__name__)

# Shared mock state cache to simulate session persistence across orchestrator steps
_MOCK_STATE = {
    "products": [
        {"product_name": "Diet Pepsi 12pk", "lost_households_pct": 14.2, "volume_change": -8.5},
        {"product_name": "Doritos Nacho Cheese 10oz", "lost_households_pct": 11.8, "volume_change": -5.2},
        {"product_name": "Campbell's Tomato Soup 10.75oz", "lost_households_pct": 9.5, "volume_change": -11.1},
        {"product_name": "Oreo Double Stuf 15.35oz", "lost_households_pct": 8.7, "volume_change": -3.4},
        {"product_name": "Lipton Iced Tea 64oz", "lost_households_pct": 7.1, "volume_change": -6.8}
    ],
    "selected_product": None,
    "audience_id": None,
    "sizing": None,
    "active_data_parts": []
}

def pricing_opportunities_tool(query_details: str) -> str:
    """Analyzes portfolio databases to identify products losing household shoppers over a 52-week pricing window.
    
    Args:
        query_details: Context string detailing target categories or portfolios.
    """
    logger.info(f"Executing pricing_opportunities_tool with details: {query_details}")
    products = _MOCK_STATE["products"]
    
    summary = "Pricing Opportunity Analysis completed successfully. Identified the following high-attrition products:\n"
    for p in products:
        summary += f"- {p['product_name']}: Lost {p['lost_households_pct']}% of households, Sales Volume change: {p['volume_change']}%\n"
        
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'product_table', 'products': products}], indent=2)}\n</a2ui-json>"
    
    return f"{summary}\n\n{a2ui_block}"

def build_audience_tool(product_name: str, spend_criteria: str = "lapsed") -> str:
    """Invokes the on-premises 'audience-build' service to isolate and construct the shopper cohort.
    
    Args:
        product_name: Name of the product (e.g. 'Diet Pepsi 12pk').
        spend_criteria: Segment definition criteria (e.g. 'lapsed', 'heavy', 'all').
    """
    logger.info(f"Executing build_audience_tool for product: {product_name} | criteria: {spend_criteria}")
    
    # Persist product context
    _MOCK_STATE["selected_product"] = product_name
    clean_name = product_name.upper().replace(' ', '-').replace("'", "")
    aud_id = f"AUD-{clean_name}-999"
    _MOCK_STATE["audience_id"] = aud_id
    
    return json.dumps({
        "status": "Created",
        "audience_id": aud_id,
        "product_name": product_name,
        "shoppers_isolated": 350000,
        "message": f"Successfully materialized cohort for {product_name} containing 350K raw historical shoppers."
    }, indent=2)

def size_audience_tool(audience_id: str, partner_options: str = "LiveRamp,Google") -> str:
    """Invokes the on-premises 'audience-size' service to calculate estimated audience reach across channels.
    
    Args:
        audience_id: The identifier of the audience segment (e.g. 'AUD-DIET-PEPSI-12PK-999').
        partner_options: Comma-separated list of target channels.
    """
    logger.info(f"Executing size_audience_tool for audience: {audience_id} | partners: {partner_options}")
    
    product_name = _MOCK_STATE["selected_product"] or "Selected Product"
    
    # Calculate mock scaling sizing
    original_size = 350000
    scaled_size = 1200000  # look-alike expansion size
    reach_pct = 85.0
    
    sizing_data = {
        "audience_id": audience_id,
        "product_name": product_name,
        "original_size": original_size,
        "scaled_size": scaled_size,
        "reach_percentage": reach_pct,
        "partners": partner_options.split(",")
    }
    
    _MOCK_STATE["sizing"] = sizing_data
    
    summary = f"Audience sizing metrics compiled successfully for ID: {audience_id}. Segment scaled from {original_size:,} raw shoppers to {scaled_size:,} estimated target households (active reach: {reach_pct}%)."
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'sizing_dashboard', 'sizing': sizing_data}], indent=2)}\n</a2ui-json>"
    
    return f"{summary}\n\n{a2ui_block}"

def activate_audience_tool(audience_id: str, partners: str) -> str:
    """Activates the given audience segment with the specified marketing partners.
    
    Args:
        audience_id: The identifier of the audience segment (e.g. 'AUD-DIET-PEPSI-12PK-999').
        partners: Comma-separated list of target channels/partners (e.g. 'LiveRamp,Google').
    """
    logger.info(f"Executing activate_audience_tool for audience: {audience_id} | partners: {partners}")
    return json.dumps({
        "status": "Success",
        "audience_id": audience_id,
        "partners": partners.split(","),
        "message": f"Successfully activated segment {audience_id} with partners {partners}. Data sync initiated."
    }, indent=2)



import uuid
import httpx
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import Message, MessageSendParams, Part, TextPart, Role, Task
from google.adk.tools import ToolContext

import os

AGENT_URLS = {
    "PricingAssortmentOrchestrator": os.environ.get(
        "PRICING_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/5098398584357781504"
    ),
    "LiquidActivateOrchestrator": os.environ.get(
        "ACTIVATE_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/2792555575144087552"
    ),
    "LoyaltyCampaignOrchestrator": os.environ.get(
        "LOYALTY_AGENT_URL", "projects/943928157761/locations/us-central1/reasoningEngines/584947332802412544"
    ),
}

_http_client = None
_genai_client = None

def _get_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None:
        headers = {}
        try:
            from google.auth import default
            from google.auth.transport.requests import Request
            credentials, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
            request = Request()
            credentials.refresh(request)
            token = credentials.token
            if token:
                headers["Authorization"] = f"Bearer {token}"
                logger.info("Successfully configured GCP access token header for remote A2A calls.")
        except Exception as e:
            logger.warning(f"Could not load application default credentials for remote auth: {e}")

        _http_client = httpx.AsyncClient(timeout=60.0, headers=headers)
    return _http_client

def _get_genai_client():
    global _genai_client
    if _genai_client is None:
        import vertexai
        from google.genai import types
        _genai_client = vertexai.Client(
            project=os.environ.get("PROJECT_ID", "shade-sandbox"),
            location=os.environ.get("LOCATION", "us-central1"),
            http_options=types.HttpOptions(api_version="v1beta1")
        )
    return _genai_client

from a2a.client import ClientFactory, ClientConfig
from a2a.types import TransportProtocol

async def send_message_tool(agent_name: str, task_summary: str, tool_context: ToolContext) -> str:
    """Delegates a specialized retail operation phase to a remote A2A-compliant agent.
    
    Args:
        agent_name: Name of the remote agent, e.g. 'PricingAssortmentOrchestrator' or 'LiquidActivateOrchestrator'.
        task_summary: Clear instructions or action commands to execute.
    """
    logger.info(f"send_message_tool: Delegating to '{agent_name}' | Task: {task_summary}")
    
    if agent_name not in AGENT_URLS:
        return f"Error: Agent '{agent_name}' is not recognized. Available agents are: {list(AGENT_URLS.keys())}"
        
    url = AGENT_URLS[agent_name]
    
    try:
        state = tool_context.state
        context_id = state.get("context_id") or str(uuid.uuid4())
        task_id = state.get("task_id") or str(uuid.uuid4())
        task_result = None

        if "projects/" in url and "reasoningEngines/" in url:
            # Route via Google GenAI SDK Agent Engines client
            logger.info(f"Routing delegation via GenAI SDK to Reasoning Engine: {url}")
            genai_client = _get_genai_client()
            agent_engine = genai_client.agent_engines.get(name=url)
            
            parts_list = [{"text": task_summary}]
            response = await agent_engine.on_message_send(
                message_id=str(uuid.uuid4()),
                role="user",
                context_id=context_id,
                parts=parts_list
            )
            if response and isinstance(response, list) and len(response) > 0:
                first_el = response[0]
                if isinstance(first_el, tuple):
                    task_result = first_el[0]
                else:
                    task_result = first_el
        else:
            # Route via standard A2A HTTP client
            logger.info(f"Routing delegation via standard HTTP REST client to: {url}")
            httpx_client = _get_client()
            config = ClientConfig(
                supported_transports=[TransportProtocol.http_json],
                httpx_client=httpx_client
            )
            client = await ClientFactory.connect(url, client_config=config)
            message = Message(
                role=Role.user,
                message_id=str(uuid.uuid4()),
                context_id=context_id,
                parts=[Part(root=TextPart(text=task_summary))]
            )
            async for event in client.send_message(message):
                if isinstance(event, tuple):
                    task_result, _ = event
                    
        if task_result is None:
            return "Error: Downstream agent returned no task updates."
            
        logger.info(f"Task status: {task_result.status.state}")
        
        # Extract messages from both status.message and history in chronological order
        agent_messages = []
        if task_result.status and task_result.status.message:
            msg = task_result.status.message
            role_str = str(msg.role).lower()
            if 'agent' in role_str or 'model' in role_str:
                agent_messages.append(msg)
                
        for msg in reversed(task_result.history or []):
            role_str = str(msg.role).lower()
            if 'user' in role_str:
                break
            if 'agent' in role_str or 'model' in role_str:
                agent_messages.append(msg)
                
        agent_messages.reverse()
        
        import re

        def _sanitize_json(s: str) -> str:
            pattern = re.compile(
                r'("literalString"\s*:\s*")(.*?)("\s*(?:\n|\r\n|\\n)?\s*\}\s*(?:\n|\r\n|\\n)?\s*\})',
                re.DOTALL
            )
            def replacer(match):
                prefix = match.group(1)
                content = match.group(2)
                suffix = match.group(3)
                content = content.replace('\n', '\\n').replace('\r', '\\r')
                content = re.sub(r'(?<!\\)"', r'\"', content)
                return prefix + content + suffix
            s = pattern.sub(replacer, s)
            s = re.sub(r'\\\s*\n', '\n', s)
            return s.strip()

        text_parts = []
        for msg in agent_messages:
            for part in msg.parts:
                print(f"[DEBUG tools.py] part type: {type(part.root)} | has_data: {hasattr(part.root, 'data')}")
                if hasattr(part.root, 'text') and part.root.text:
                    text_val = part.root.text
                    
                    # Extract any <a2ui-json> blocks
                    a2ui_pattern = re.compile(r'<a2ui-json>(.*?)</a2ui-json>', re.DOTALL)
                    for match in a2ui_pattern.finditer(text_val):
                        try:
                            json_str = _sanitize_json(match.group(1))
                            payloads = json.loads(json_str)
                            
                            # Import builders dynamically to avoid circular import issues
                            try:
                                from .components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
                            except ImportError:
                                from components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
                            
                            def process_payload(payload):
                                comp_type = payload.get("component_type")
                                if comp_type == "product_table":
                                    full_a2ui_str = get_product_table_a2ui(payload["products"])
                                    full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                    full_payload = json.loads(full_json_str)
                                    for sub_p in full_payload:
                                        _MOCK_STATE["active_data_parts"].append(sub_p)
                                elif comp_type == "sizing_dashboard":
                                    full_a2ui_str = get_sizing_dashboard_a2ui(payload["sizing"])
                                    full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                    full_payload = json.loads(full_json_str)
                                    for sub_p in full_payload:
                                        _MOCK_STATE["active_data_parts"].append(sub_p)
                                elif comp_type == "loyalty_dashboard":
                                    full_a2ui_str = get_loyalty_dashboard_a2ui(payload["loyalty"])
                                    full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                    full_payload = json.loads(full_json_str)
                                    for sub_p in full_payload:
                                        _MOCK_STATE["active_data_parts"].append(sub_p)
                                else:
                                    _MOCK_STATE["active_data_parts"].append(payload)

                            if isinstance(payloads, list):
                                for p in payloads:
                                    process_payload(p)
                            else:
                                process_payload(payloads)
                            logger.info("[tools.py] Extracted, expanded and cached A2UI block from sub-agent text.")
                        except Exception as parse_ex:
                            logger.warning(f"[tools.py] Failed to parse/expand extracted A2UI block: {parse_ex}")
                    
                    # Strip <a2ui-json> blocks from the text returned to LLM
                    clean_text = a2ui_pattern.sub("", text_val).strip()
                    if clean_text:
                        text_parts.append(clean_text)
                elif hasattr(part.root, 'data') and part.root.data:
                    data_val = part.root.data
                    print(f"[DEBUG tools.py] Caching data part: {list(data_val.keys())}")
                    
                    try:
                        from .components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
                    except ImportError:
                        from components import get_product_table_a2ui, get_sizing_dashboard_a2ui, get_loyalty_dashboard_a2ui
                        
                    comp_type = data_val.get("component_type")
                    if comp_type:
                        try:
                            if comp_type == "product_table":
                                full_a2ui_str = get_product_table_a2ui(data_val["products"])
                                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                full_payload = json.loads(full_json_str)
                                for sub_p in full_payload:
                                    _MOCK_STATE["active_data_parts"].append(sub_p)
                            elif comp_type == "sizing_dashboard":
                                full_a2ui_str = get_sizing_dashboard_a2ui(data_val["sizing"])
                                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                full_payload = json.loads(full_json_str)
                                for sub_p in full_payload:
                                    _MOCK_STATE["active_data_parts"].append(sub_p)
                            elif comp_type == "loyalty_dashboard":
                                full_a2ui_str = get_loyalty_dashboard_a2ui(data_val["loyalty"])
                                full_json_str = full_a2ui_str.replace("<a2ui-json>", "").replace("</a2ui-json>", "").strip()
                                full_payload = json.loads(full_json_str)
                                for sub_p in full_payload:
                                    _MOCK_STATE["active_data_parts"].append(sub_p)
                            else:
                                _MOCK_STATE["active_data_parts"].append(data_val)
                            logger.info(f"[tools.py] Expanded and cached native DataPart component: {comp_type}")
                        except Exception as expand_ex:
                            logger.warning(f"[tools.py] Failed to expand native DataPart: {expand_ex}")
                            _MOCK_STATE["active_data_parts"].append(data_val)
                    else:
                        _MOCK_STATE["active_data_parts"].append(data_val)
                        
        if not text_parts:
            return "Error: Downstream agent completed successfully but returned no parts in history."
            
        return "\n".join(text_parts)
        
    except Exception as e:
        logger.error(f"Failed to delegate task to A2A agent '{agent_name}': {e}", exc_info=True)
        return f"Error delegating task to '{agent_name}': {str(e)}"

def get_loyalty_options_tool(product_name: str) -> str:
    """Retrieves current loyalty segment size and risk levels for personalization campaigns.
    
    Args:
        product_name: Name of the product (e.g. 'Diet Pepsi 12pk').
    """
    logger.info(f"Executing get_loyalty_options_tool for: {product_name}")
    loyalty_data = {
        "product_name": product_name,
        "shoppers_isolated": 350000,
        "risk_level": "High"
    }
    
    try:
        from .components import get_loyalty_dashboard_a2ui
    except ImportError:
        from components import get_loyalty_dashboard_a2ui
        
    summary = f"Successfully compiled loyalty segment parameters for product: {product_name}. Launch campaign when ready."
    a2ui_block = f"<a2ui-json>\n{json.dumps([{'component_type': 'loyalty_dashboard', 'loyalty': loyalty_data}], indent=2)}\n</a2ui-json>"
    
    return f"{summary}\n\n{a2ui_block}"

def launch_campaign_tool(product_name: str, discount_pct: float, points_mult: float) -> str:
    """Launches the personalized loyalty rewards campaign targeting lapsed customers.
    
    Args:
        product_name: Name of the product.
        discount_pct: The percent discount rate (e.g., 10 or 15).
        points_mult: Multiplier factor for reward points earned (e.g., 2 or 3).
    """
    logger.info(f"Executing launch_campaign_tool for {product_name}: discount={discount_pct}%, points={points_mult}x")
    return json.dumps({
        "status": "Success",
        "product_name": product_name,
        "discount_pct": discount_pct,
        "points_mult": points_mult,
        "message": f"Successfully launched personalized campaign for {product_name} cohort (discount: {discount_pct}%, points multiplier: {points_mult}x)!"
    }, indent=2)


