# Retail Multi-Agent Orchestration Hub & Gemini Enterprise Agent Engine Integration

The **Retail Multi-Agent Orchestration Hub** is a premium, state-of-the-art pilot portal demonstrating a conversational AI interface coupled with an interactive sandbox canvas. The system coordinates retail pricing analytics, cohort construction, audience sizing, and marketing activations across a hybrid multi-agent network.

---

## 🎥 Web Application Demo Walkthrough

Explore the E2E user flow of the Multi-Agent Portal, showing session initialization, tool execution, dynamic widget rendering, and safety blocks:

![Web App Demo Walkthrough](architecture/videos/portal_demo.webp)

---

## 1. System Architecture & Topology

The application is built on the **Gemini Enterprise Agent Engine**, implementing a secure, stateful multi-agent hierarchy governed by Model Armor and integrated with custom tools via the Model Context Protocol (MCP):

![Circana Multi-Agent System Architecture](architecture/screenshots/system_architecture_v3.png)

### Core Architecture Components

1.  **FastAPI Portal App & HTTP Sessions:** Manages local user sessions, authenticates identity against Google/Entra Identity Providers, and maintains conversation states locally before dispatching payloads downstream.
2.  **Model Armor Safety Shield:** Acts as an inline firewall for the LLM. Every user prompt is scanned for prompt injection, hate speech, and jailbreak vectors. Every agent output is scanned to redact sensitive PII (Social Security or Credit Card numbers).
3.  **Gemini Enterprise Agent Engine:** Google Cloud's serverless container runtime that packages python-based agent orchestration frameworks and executes them securely under IAM policies.
4.  **Agent & MCP Registry:** Centralized registries that host global metadata configurations. The **Agent Registry** catalog allows the Supervisor to discover sub-agent microservice endpoints, and the **MCP Registry** publishes the schemas of tools hosted on external MCP servers.
5.  **A2A (Agent-to-Agent) Protocol:** Structured JSON message schema that allows the Supervisor to pass structured tasks and raw parameter definitions to sub-agents (and vice-versa) using A2A `DataPart` slots instead of raw unstructured text.
6.  **A2UI (Agent-to-User-Interface) Protocol:** Formats widget schemas (`<a2ui-json>`) returned by agents. The Supervisor intercepts these declarations and expands them into premium HTML widget sandboxes before streaming them to the client console.
7.  **Circana MCP Server on Cloud Run:** Host service built to run the Model Context Protocol in the cloud. It wraps our custom Audience Builder database APIs into standard MCP JSON-RPC schemas and exposes them safely via HTTPS.
8.  **Sessions & Memory Bank:** Manages session state preservation across chat turns. Integrates short-term session memory for conversation context with the **Gemini Enterprise Memory Bank** to extract and recall long-term user preferences and campaign history across browser reloads.
9.  **Agent Observability & Cloud Logging:** Emits execution telemetry, network latency, token consumption, and safety violations directly to **GCP Cloud Logging** to enable full tracing of A2A calls and tool usage per transaction step.
10. **Agent Identity (SPIFFE ID):** Native GCP IAM security protocol assigning cryptographically-attested SPIFFE IDs to each sub-agent for fine-grained authorization and auditing.

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
*   **Live Proof-of-Registration (Agent Catalog):**
    ![GCP Agent Registry Catalog](architecture/screenshots/agent_registry_list.png)

### ⚙️ Gemini Enterprise Agent Engine
*   **Definition:** A managed runtime environment that packages Python code, dependencies, and parameters into a serialized execution graph (via Cloudpickle) and deploys it as an API endpoint.
*   **System Integration:** All three Circana sub-agents are deployed as Cloud Agent Engine endpoints under Python 3.13 containers:
    *   **Pricing Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/5913690854400196608`
    *   **Activate Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/3977143014630883328`
    *   **Loyalty Engine:** `projects/943928157761/locations/us-central1/reasoningEngines/4675200956873310208`
*   **Official Citation:**
    > *"Gemini Enterprise Agent Engine lets you deploy python-based orchestration frameworks (such as LangChain or custom agent models) to Google Cloud as fully-managed endpoints."* — [Google Cloud Gemini Enterprise Agent Engine Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/reasoning-engine/overview)
*   **Live Proof-of-Deployment (Agent Engine Endpoints):**
    ![GCP Agent Engine Registered Endpoints](architecture/screenshots/agent_engine_registered.png)

### 🪪 GCP Agent Identity (SPIFFE ID)
*   **Definition:** A purpose-built, native IAM security protocol that assigns unique, cryptographically-attested SPIFFE identities to deployed AI agents. This avoids the use of shared, over-privileged master service account keys and enables granular audit logs.
*   **System Integration:** All Circana sub-agents are deployed with `"identity_type": "AGENT_IDENTITY"`, binding their runtime permissions strictly to their individual execution scopes.
*   **Official Citation:**
    > *"Agent Identity provides a strongly attested, SPIFFE-based cryptographic identity for each individual agent... This promotes a least-privilege approach to agent permissions, bounding access tokens to the agent runtime and ensuring non-repudiable auditing of agent actions."* — [Google Cloud Gemini Enterprise Agent Platform Security Guide](https://cloud.google.com/vertex-ai/generative-ai/docs/agent-platform/security)


### 👥 Multi-Agent Teamwork Topology & Active Registry
The system utilizes a hub-and-spoke supervisor pattern. The root supervisor orchestrates the pipeline phases, parses A2UI layout responses, and coordinates state transitions.

```mermaid
graph TD
    User([User Interface / Session]) -->|1. Chat/Callback Event| Supervisor[CircanaPilotSupervisor]
    
    Supervisor -->|2a. Delegate Phase A| Pricing[PricingAssortmentOrchestrator]
    Supervisor -->|2b. Delegate Phase B/C| Activate[LiquidActivateOrchestrator]
    Supervisor -->|2c. Delegate Phase D| Loyalty[LoyaltyCampaignOrchestrator]
    
    Pricing -->|Query Attrition| Tool1[pricing_opportunities_tool]
    Activate -->|Compute Sizing| Tool2[audience_sizing_tool]
    Activate -->|Sync Segment| Tool3[activate_segment_tool]
    Loyalty -->|Fetch Offer Config| Tool4[get_loyalty_options_tool]
    Loyalty -->|Launch Rewards| Tool5[launch_campaign_tool]
    
    style Supervisor fill:#f8fafc,stroke:#002f6c,stroke-width:2px;
    style Pricing fill:#e0f2fe,stroke:#0284c7,stroke-width:1px;
    style Activate fill:#ecfdf5,stroke:#059669,stroke-width:1px;
    style Loyalty fill:#fffbeb,stroke:#d97706,stroke-width:1px;
```

#### Active Registry Topology

| Agent Name | Role & Objective | Deployed Endpoint (Vertex AI) | Exposed Skills |
| :--- | :--- | :--- | :--- |
| **CircanaPilotSupervisor** | Root coordinator supervising the multi-agent pipeline and managing session state. | *Local web server executor* | Pipeline routing, callback execution, A2UI normalization. |
| **PricingAssortmentOrchestrator** | specialist agent identifying pricing opportunities and category buyer loss. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`5913690854400196608` | Portfolio search, category shopper attrition mapping. |
| **LiquidActivateOrchestrator** | specialist agent coordinating cohort audience sizing and activation exports. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`3977143014630883328` | Audience sizing, LiveRamp/Google Customer Match sync. |
| **LoyaltyCampaignOrchestrator** | specialist agent customizing personalization parameters and reward launches. | `projects/943928157761/`<br>`locations/us-central1/`<br>`reasoningEngines/`<br>`4675200956873310208` | Campaign personalization, loyalty rewards activation. |

> [!IMPORTANT]
> **Stateful Context Memory**: In the local development runner, session state is managed via `InMemoryMemoryService`. 
> While this works for single-process local debugging, deploying sub-agents to multi-worker or cloud environments requires migrating to **Firestore-based memory (`FirestoreMemoryService`)** to prevent containers from losing conversation context ("amnesia") between successive user prompts.

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

registry = AgentRegistry(project_id=GOOGLE_CLOUD_PROJECT, location="global")
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
* **Observability Metrics**: The Vertex AI Agent Platform dashboard tracks queries per second, latency profiles, error rates, and container system resources:

  ![Agent Observability Dashboard Metrics](architecture/screenshots/agent_observability_metrics.png)

![GCP Cloud Run Request Logs](architecture/screenshots/cloud_run_mcp_logs.png)

---

### E. Stateful Sessions & Playground Testing
The Gemini Enterprise Agent Engine maintains conversational state natively across multi-turn interactions. Developers can monitor active sessions and inspect complete step-by-step chat logs and tool invocations:
* **Sessions Registry**: Active conversation sessions are tracked per reasoning engine:

  ![Agent Engine Sessions Registry](architecture/screenshots/agent_engine_sessions.png)

* **Playground Trace Inspection**: Complete interaction histories, tool calls, and state transitions can be audited in the Agent Playground:

  ![Agent Engine Playground Trace](architecture/screenshots/agent_engine_playground.png)

---

## 6. Setup & Deployment Guide from Scratch

This guide walks through deploying the entire Multi-Agent platform and MCP tool ecosystem from scratch on Google Cloud Platform.

### 📋 Prerequisites
1. **Google Cloud SDK**: Install the `gcloud` CLI. Authenticate your CLI and set up Application Default Credentials (ADC):
   ```bash
   gcloud auth login
   gcloud auth application-default login
   ```
2. **Project Configuration**: Ensure your target GCP project (e.g., `shade-sandbox`) is active, with Vertex AI, Cloud Run, and Cloud Storage APIs enabled.
3. **Environment Setup**: Ensure Python 3.13 is installed. Create and activate a virtual environment, then install requirements:
   ```bash
   python3.13 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

### 🚀 Step-by-Step Setup

#### Step 1: Deploy the MCP Tool Server to Cloud Run
The MCP server hosts the audience building database querying engines. It must be deployed first so the sub-agents can fetch its endpoint.

1. Ensure the `deploy_mcp.py` script is configured with your target GCP `project_id` and preferred deployment `region`.
2. Run the deployment script:
   ```bash
   python deploy_mcp.py
   ```
   *This command uploads the local MCP workspace, builds a container on Google Cloud Run, deploys it securely (disallowing public unauthenticated access), and updates your `.env` file with the generated `MCP_SERVER_URL`.*

---

#### Step 2: Deploy Orchestrator Sub-Agents to Vertex AI
Once the MCP server is live, the specialist sub-agents (Pricing, Activate, Loyalty) must be packaged and deployed as managed Reasoning Engine endpoints.

1. Set the staging GCS bucket variable in your environment or `.env` file:
   ```env
   STORAGE_BUCKET=gs://shade-agent-staging
   ```
2. Run the deployment script:
   ```bash
   python deploy.py
   ```
   *This script packages the local agent modules (under the `circana_pilot_agent` namespace), bundles dependencies (like `a2a-sdk` and `google-genai`), serializes the agent graphs, uploads them to your GCS staging bucket, creates Vertex AI Reasoning Engine resources, and automatically updates your local `.env` file with the new resource URLs (`PRICING_AGENT_URL`, `ACTIVATE_AGENT_URL`, `LOYALTY_AGENT_URL`).*

   > [!IMPORTANT]
   > **Packaging Directory Structure**: The `circana_pilot_agent` directory contains the sub-agent definitions, tools, and the `examples/` subdirectory. Packaging the entire `circana_pilot_agent` folder as an `extra_package` guarantees that relative file resource queries (like searching for A2UI schemas in `examples/0.8`) resolve correctly inside the cloud reasoning container.

---

#### Step 3: Run the Local Web Application
With all remote APIs and sub-agent endpoints successfully deployed and synchronized in your local `.env` file, start the local FastAPI web server:

1. Launch the web application using uvicorn:
   ```bash
   uvicorn web_app.server:app --host 0.0.0.0 --port 8000
   ```
2. Open your browser and navigate to `http://localhost:8000` to interact with the visual orchestrator portal.

---

### 🧹 Step 4: Maintenance & Utilities
*   **Decoy/Stale Engine Cleanup**: To avoid resource leaks and clean up old/orphaned reasoning engine deployments:
    ```bash
    python scripts/delete_unused_engines.py
    ```
```
This utility fetches all active reasoning engine deployments, matches them against the current IDs declared in your `.env` configuration, and rate-limits the deletion of any unreferenced/orphaned engines in the GCP project.

