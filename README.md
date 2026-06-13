# Retail Multi-Agent Orchestration Hub & Gemini Enterprise Agent Engine Integration

The **Retail Multi-Agent Orchestration Hub** is a premium, state-of-the-art pilot portal demonstrating a conversational AI interface coupled with an interactive sandbox canvas. The system coordinates retail pricing analytics, cohort construction, audience sizing, and marketing activations across a hybrid multi-agent network.

---

## 🎥 Web Application Demo Walkthrough

Explore the E2E user flow of the Multi-Agent Portal, showing session initialization, tool execution, dynamic widget rendering, and safety blocks:

![Web App Demo Walkthrough](architecture/videos/portal_demo.webp)

---

## 1. System Architecture & Topology

The application is built on the **Gemini Enterprise Agent Engine**, implementing a secure, stateful multi-agent hierarchy governed by Model Armor and integrated with custom tools via the Model Context Protocol (MCP):

```mermaid
graph TD
    subgraph Client Layer [Client Console]
        User([Marketer Console]) <-->|HTTPS / HTML Widgets| Portal[FastAPI Portal App]
        PortalDB[(Local HTTP Session Store)] <--> Portal
    end

    subgraph GCP Agent Platform [Gemini Enterprise Agent Engine Zone]
        direction TB
        subgraph Security Gate [GCP Safety Filter]
            ModelArmor{Model Armor Safety Shield}
        end
        
        subgraph Runtime [Gemini Enterprise Agent Engine]
            direction TB
            Supervisor["Supervisor Agent (PilotSupervisor)"]
            
            subgraph Pricing Service [Pricing Assortment Orchestrator]
                PricingOrch["Pricing Orchestrator Agent"]
                SemanticAgent["Semantic Layer Agent"]
                PricingOppAgent["Pricing Opportunities Agent"]
            end
            
            subgraph Activation Service [Liquid Activate Orchestrator]
                ActivateOrch["Activation Orchestrator Agent"]
                BuildAgent["Audience Build Agent"]
                SizeAgent["Audience Size Agent"]
                ScaleAgent["Audience Scale Agent (Stub)"]
            end

            subgraph Decoys [Precision Routing Verification]
                LoyaltyOrch["Loyalty Campaign Agent (Decoy)"]
            end
        end

        subgraph Directory [GCP Platform Registries]
            AgentRegistry[Agent Registry: Agent Catalog]
            MCPRegistry[MCP Registry: Tool Catalog]
        end
    end

    subgraph Integration Layer [Managed Integration Zone]
        CloudRunMCP["Circana MCP Server (Cloud Run)"]
        OnPremDB[(Circana Shopper Database)]
        PricingAPI[Circana Pricing REST API]
    end

    %% Communication Flow
    User -->|1. Prompt Input| Portal
    Portal -->|2. Sanitize Prompt| ModelArmor
    ModelArmor -->|3. Route Prompt| Supervisor
    Supervisor -.->|Query Catalog| AgentRegistry
    
    %% Orchestration Delegation (A2A)
    Supervisor ===>|A2A Protocol| PricingOrch
    Supervisor ===>|A2A Protocol| ActivateOrch
    Supervisor -.->|Decoy Route Validation| LoyaltyOrch
    
    PricingOppAgent -->|Query Metrics| PricingAPI
    BuildAgent -.->|Resolve Tool| MCPRegistry
    SizeAgent -.->|Resolve Tool| MCPRegistry
    
    BuildAgent ==>|SSE JSON-RPC| CloudRunMCP
    SizeAgent ==>|SSE JSON-RPC| CloudRunMCP
    CloudRunMCP -->|SQL Query| OnPremDB
    
    %% UI Projection (A2UI)
    Supervisor -->|4. Template Expansion| Portal
    Portal -->|5. Render iframe Sandbox| User

    %% Style Definitions
    classDef client fill:#E1F5FE,stroke:#03A9F4,stroke-width:2px,color:#01579B;
    classDef security fill:#FFEBEE,stroke:#EF5350,stroke-width:2px,color:#B71C1C;
    classDef runtime fill:#E8F5E9,stroke:#4CAF50,stroke-width:2px,color:#1B5E20;
    classDef registry fill:#FFF8E1,stroke:#FFC107,stroke-width:2px,color:#FF6F00;
    classDef database fill:#EDE7F6,stroke:#673AB7,stroke-width:2px,color:#4A148C;

    class User,Portal,PortalDB client;
    class ModelArmor security;
    class Supervisor,PricingOrch,SemanticAgent,PricingOppAgent,ActivateOrch,BuildAgent,SizeAgent,ScaleAgent,LoyaltyOrch runtime;
    class AgentRegistry,MCPRegistry registry;
    class CloudRunMCP,OnPremDB,PricingAPI database;
```

### Core Architecture Components

1.  **FastAPI Portal App & HTTP Sessions:** Manages local user sessions, authenticates identity against Google/Entra Identity Providers, and maintains conversation states locally before dispatching payloads downstream.
2.  **Model Armor Safety Shield:** Acts as an inline firewall for the LLM. Every user prompt is scanned for prompt injection, hate speech, and jailbreak vectors. Every agent output is scanned to redact sensitive PII (Social Security or Credit Card numbers).
3.  **Gemini Enterprise Agent Engine:** Google Cloud's serverless container runtime that packages python-based agent orchestration frameworks and executes them securely under IAM policies.
4.  **Agent & MCP Registry:** Centralized registries that host global metadata configurations. The **Agent Registry** catalog allows the Supervisor to discover sub-agent microservice endpoints, and the **MCP Registry** publishes the schemas of tools hosted on external MCP servers.
5.  **A2A (Agent-to-Agent) Protocol:** Structured JSON message schema that allows the Supervisor to pass structured tasks and raw parameter definitions to sub-agents (and vice-versa) using A2A `DataPart` slots instead of raw unstructured text.
6.  **A2UI (Agent-to-User-Interface) Protocol:** Formats widget schemas (`<a2ui-json>`) returned by agents. The Supervisor intercepts these declarations and expands them into premium HTML widget sandboxes before streaming them to the client console.
7.  **Circana MCP Server on Cloud Run:** Host service built to run the Model Context Protocol in the cloud. It wraps our custom Audience Builder database APIs into standard MCP JSON-RPC schemas and exposes them safely via HTTPS.

---

## 2. Master Sequence Flow

The following sequence diagram details how user inputs are processed, sanitized, delegated via A2A, checked for Human-in-the-Loop constraints, and projected onto the UI via A2UI widgets:

```mermaid
sequenceDiagram
    autonumber
    actor Marketer as Marketer
    participant Portal as FastAPI Portal App
    participant Armor as Model Armor Safety Shield
    participant Supervisor as Supervisor Agent (Agent Engine)
    participant SubAgent as Orchestrator Agent (Agent Engine)
    participant MCP as Circana MCP Server (Cloud Run)
    participant DB as Shopper DB / API

    %% Phase A: Initial Query & Pricing Analysis
    Marketer->>Portal: Input: "Identify soft drink pricing opportunities"
    Portal->>Armor: Validate Input & check Jailbreaks
    Note over Armor: Screens for prompt injections / jailbreaks
    Armor-->>Portal: Content Safety: ALLOWED
    Portal->>Supervisor: Execute Chat Turn
    Supervisor->>SubAgent: Delegate pricing analysis (A2A Protocol)
    SubAgent->>DB: Query attrition product catalog
    DB-->>SubAgent: Return product metrics JSON
    SubAgent-->>Supervisor: Return structured widget layout (<a2ui-json>)
    Supervisor-->>Portal: Stream text response + raw JSON widget data
    Note over Portal: Compiles raw JSON into HTML template with local CSS
    Portal-->>Marketer: Render Pricing Table Widget (HITL Checkpoint)

    %% Phase B: Human-in-the-Loop Callback & Audience Sizing
    Marketer->>Portal: Click "Select Cohort" for Diet Pepsi 12pk
    Note over Portal: Formulates semantic trigger: "Action: size Pepsi cohort"
    Portal->>Supervisor: Post Action Callback Event
    Supervisor->>SubAgent: Delegate audience construction & sizing (A2A)
    SubAgent->>MCP: Call tool: "audience-build"
    MCP->>DB: Materialize buyer segment
    DB-->>MCP: Segment materialized (AUD-PEPSI-999)
    MCP-->>SubAgent: Tool success payload
    SubAgent->>MCP: Call tool: "audience-size" (Params: AUD-PEPSI-999)
    MCP->>DB: Estimate audience size & reach
    DB-->>MCP: Return sizing numbers (1,200,000 households)
    MCP-->>SubAgent: Tool success payload
    SubAgent-->>Supervisor: Return structured sizing widget data
    Supervisor-->>Portal: Stream sizing metrics response
    Portal-->>Marketer: Render Interactive Cohort Sizing Dashboard

    %% Phase C: Activation Sync Export
    Marketer->>Portal: Check "LiveRamp" and click "Activate"
    Portal->>Supervisor: Post Activation Action Callback
    Supervisor->>SubAgent: Delegate activation export sync
    SubAgent->>DB: Execute export job to LiveRamp
    DB-->>SubAgent: Sync job initialized successfully
    SubAgent-->>Supervisor: Task complete success payload
    Supervisor-->>Portal: Stream sync confirmation text
    Portal-->>Marketer: Display final success message
```

---

## 3. Gemini Enterprise Agent Engine Component References & Citations

### 🛡️ Model Armor
*   **Definition:** A managed safety service designed to serve as a guardrail wrapper around LLM prompts and responses. It screens input strings for prompt injection, jailbreak attempts, and toxic content, and redacts sensitive Personally Identifiable Information (PII) before it reaches the model.
*   **System Integration:** Our supervisor uses Model Armor to sanitize user prompts inline. Any jailbreak string is immediately blocked, raising a validation exception.
*   **Official Citation:** 
    > *"Vertex AI Model Armor helps protect your generative AI models by scanning inputs and outputs for prompt injections, jailbreaks, PII, and unsafe content."* — [Google Cloud Vertex AI Model Armor Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/model-armor)
*   **Live Proof-of-Safety (Prompt Injection Blocked):**
    ![Model Armor Blocked Prompt](architecture/screenshots/model_armor_prompt_block.png)

### 🗃️ Agent Registry & MCP tool registry
*   **Definition:** The centralized catalog in Gemini Enterprise Agent Engine where custom tools, endpoints, and Model Context Protocol (MCP) servers are registered, authorized, and made discoverable.
*   **System Integration:** The `circana-mcp-server` is registered under the global Agent Registry services with protocol bindings for `JSONRPC` over HTTP/SSE, publishing our custom cohort building tools.
*   **Official Citation:**
    > *"Agent Registry provides a unified catalog to discover, govern, and reuse tools, APIs, and Model Context Protocol servers across your enterprise AI applications."* — [Google Cloud Agent Platform Registry Documentation](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-registry)
*   **Live Proof-of-Registration (MCP Registry):**
    ![GCP MCP Server Registration](architecture/screenshots/gcp_mcp_server_registered.png)

### ⚙️ Gemini Enterprise Agent Engine
*   **Definition:** A managed runtime environment that packages Python code, dependencies, and parameters into a serialized execution graph (via Cloudpickle) and deploys it as an API endpoint.
*   **System Integration:** All three Circana sub-agents are deployed as Cloud Agent Engine endpoints under Python 3.13 containers:
    *   **Pricing Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/3371690339726262272`
    *   **Activate Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/1265131614023712768`
    *   **Loyalty Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/7172728425226960896`
*   **Official Citation:**
    > *"Gemini Enterprise Agent Engine lets you deploy python-based orchestration frameworks (such as LangChain or custom agent models) to Google Cloud as fully-managed endpoints."* — [Google Cloud Gemini Enterprise Agent Engine Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/reasoning-engine/overview)
*   **Live Proof-of-Deployment (Agent Engine Endpoints):**
    ![GCP Agent Engine Registered Endpoints](architecture/screenshots/agent_engine_registered.png)

---

## 4. E2E Execution Flow & Interactive Dashboards

### Step A: Identify Pricing Opportunities
The supervisor delegates the initial query to the **Pricing Agent**, which queries historical store attrition data and projects an interactive product selection table into the browser canvas:

![Initial Product Select Table](architecture/screenshots/web_pricing_table.png)

---

### Step B: Audience Sizing Dashboard
Clicking **Select Cohort** on the widget triggers a Human-in-the-Loop callback. The supervisor invokes the **Activation Agent**, which executes tools on the registered `circana-mcp-server` Cloud Run instance. Sizing counts and activation channel selections are rendered on a polished dashboard card:

![Interactive Cohort Sizing Dashboard](architecture/screenshots/sizing_dashboard_verified.png)

---

### Step C: Export Sync Confirmation
Upon selecting the channels (LiveRamp, Google Customer Match) and clicking **Activate**, the agent runs the export tool and writes success events back to the session logger:

![Sync Confirmation Success](architecture/screenshots/web_final_success.png)

---

## 5. Advanced Cloud Platform Integration Details

### A. MCP Cloud Run Deployment & Agent Registry Integration
The Circana Model Context Protocol (MCP) server is compiled as a Docker container (refer to [Dockerfile](file:///usr/local/google/home/elhadik/Circana_POC/Dockerfile)) running FastAPI in HTTP mode. The container is deployed to Google Cloud Run with access control secured by default (`--no-allow-unauthenticated`). 

To orchestrate tool calling securely, we utilize the **Gemini Enterprise Agent Engine Registry** client. During agent initialization, the agent dynamically fetches the registered tool descriptions and connection endpoints:
```python
from google.adk.integrations.agent_registry import AgentRegistry

registry = AgentRegistry(project_id=PROJECT_ID, location="global")
mcp_toolset = registry.get_mcp_toolset(MCP_SERVER_RESOURCE_NAME)
```
The ADK library automatically resolves the JSON-RPC SSE/Streamable HTTP bindings, manages connection pooling, and handles OIDC identity token generation for Cloud Run secure request routing via a custom `header_provider`.

---

### B. Gemini Enterprise Agent Engine & Graph Orchestration
We leverage the **Google GenAI ADK 2** framework to construct our multi-agent execution graph. Rather than relying on open-ended, non-deterministic agent routing, our topology enforces a strict **state-machine graph** via prompt instructions, structured payloads, and specialized node routing.

#### 1. Graph Structure & Node Definition
The orchestration graph is implemented as a hub-and-spoke tree:
* **Root Node (Supervisor)**: The `CircanaPilotSupervisor` agent (defined in [agent.py](file:///usr/local/google/home/elhadik/Circana_POC/agents/circana_pilot_agent/agent.py)) coordinates user session contexts, delegates tasks to specific leaf nodes, and projects UI widgets back to the portal.
* **Leaf Nodes (Sub-Agents)**: Remote `Agent` microservices deployed on the Gemini Enterprise Agent Engine (e.g., `PricingAssortmentOrchestrator`, `LiquidActivateOrchestrator`, and `LoyaltyCampaignOrchestrator`).

#### 2. Deterministic State Transitions
We map user interactions to a series of four distinct operational phases, preventing the supervisor from diverging or skipping steps:
* **Phase A (Pricing Analysis)** $\rightarrow$ **HITL Checkpoint** $\rightarrow$ **Phase B (Audience Sizing)** $\rightarrow$ **Phase C (Activation Sync)** $\rightarrow$ **Phase D (Loyalty Campaign)**

This state machine is enforced programmatically in the Supervisor's system instruction template (refer to [agent.py:L20-38](file:///usr/local/google/home/elhadik/Circana_POC/agents/circana_pilot_agent/agent.py#L20-38)):
1. **State Isolation**: Sub-agents only have access to tools that belong to their specific domain. For instance, the `PricingOpportunitiesAgent` cannot trigger audience activation.
2. **Context Passing (A2A)**: The root node passes parameters (such as the target cohort product or activation partners) down to the leaf nodes using structured A2A data slots, avoiding unstructured instruction drift.
3. **Execution Thread Locking**: The supervisor is instructed to halt execution and return control to the portal after completing each phase's A2UI component rendering, waiting for explicit user interaction before transitioning to the next phase.

#### 3. Dynamic Hybrid Routing vs. get_remote_a2a_agent
While standard Gemini Enterprise Agent Registry console examples recommend abstracting remote nodes using:
```python
remote_agent = registry.get_remote_a2a_agent(AGENT_NAME)
sub_agents=[remote_agent]
```
we programmatically route sub-agent communications through a custom `send_message_tool` tool instead. This dynamic approach guarantees:
* **Local Emulation Support**: When developing/testing locally, the supervisor routes requests to local mock ports (e.g. `http://localhost:8001`), whereas `get_remote_a2a_agent` would always force routing to cloud deployments.
* **Identity Header Propagation**: We can inject user Microsoft Entra ID context dynamically in A2A request headers per turn.

---

### C. Human-in-the-Loop (HITL) State Suspension & A2UI widgets
To provide a premium, application-like experience rather than a basic text chat, we leverage the **A2UI (Agent-to-User-Interface) Web Component** framework. 

#### 1. Rich Interactive Web Canvas
A2UI allows agents to project full-featured, stateful HTML/JS widgets directly into the user console interface:
* **Interactive Components**: Agents construct structured JSON configurations defining tables, charts, and control panels (badges, sliders, checkboxes).
* **Hover-over Tooltips**: Visual charts (such as the Reach Distribution graphs) render tooltips and details dynamically as the user hovers.
* **Interactive Elements**: Users can select checkable partners (e.g. checking "LiveRamp" or "Google Customer Match" in the sizing dashboard), toggle configurations, and edit pricing rows.
* **State Synchronization**: Actions taken in the sandboxed widget (clicks, toggles) immediately synchronize with the local session state.

#### 2. Suspension & Resumption Flow
This interaction is governed by state suspension and callback execution:
1. **Suspension**: When the Pricing Agent identifies cohort opportunities, it halts the execution graph and returns a structured `<a2ui-json>` schema block to the supervisor.
2. **Dynamic Rendering**: The frontend portal parses this block and renders a custom interactive sandbox.
3. **Resumption**: When the user performs an action (e.g., clicking a button inside the pricing table or clicking "Activate" after checking destination partners), the portal intercepts the click event and POSTs a resume callback request back to the `SupervisorAgent`, triggering the next node in the multi-agent graph.

---

### D. GCP Cloud Logging & Security Auditing
All session telemetries, tool executions, and safety screenings are logged natively to **GCP Cloud Logging**:
* **Execution Telemetry**: Trace IDs are propagated across the A2A network, matching Supervisor delegation steps with Cloud Run MCP container requests.
* **Cost Auditing**: Token consumption details and model latency are written per turn for exact cost computation.
* **Audit Traces**: Cloud Run request logs monitor endpoint access, rejecting unauthenticated requests automatically.

![GCP Cloud Run Request Logs](architecture/screenshots/cloud_run_mcp_logs.png)

---

## 6. Local Web App Setup & Execution

### Prerequisites
*   Python 3.13 Virtual Environment (`.venv`)
*   Google Cloud SDK initialized on project `shade-sandbox`.

### Step 1: Environment Variables Setup
Initialize `.env` in the project root:
```env
GOOGLE_GENAI_USE_VERTEXAI=true
GOOGLE_CLOUD_PROJECT=shade-sandbox
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_GENAI_MODEL=gemini-2.5-flash

# Cloud Run MCP Server Url
MCP_SERVER_URL=https://circana-mcp-server-943928157761.us-central1.run.app

# Deployed Gemini Enterprise Agent Engine Resource IDs
PRICING_AGENT_URL=projects/943928157761/locations/us-central1/reasoningEngines/3371690339726262272
ACTIVATE_AGENT_URL=projects/943928157761/locations/us-central1/reasoningEngines/1265131614023712768
LOYALTY_AGENT_URL=projects/943928157761/locations/us-central1/reasoningEngines/7172728425226960896
```

### Step 2: Start the Web Portal App
Run the dev server locally using the active virtual environment:
```bash
source .venv/bin/activate
uvicorn web_app.server:app --host 0.0.0.0 --port 8000
```
Open your browser and navigate to `http://localhost:8000` to start orchestrating.
