---
name: agent-identity-setup
description: Guides configuring native AGENT_IDENTITY for Reasoning Engines to secure access using SPIFFE cryptographic IDs.
---
# Agent Identity Setup Skill

This skill documents how to deploy AI agents on the Gemini Enterprise Agent Engine runtime using secure, native cryptographic identities instead of shared service account keys.

## Core Concepts
*   **AGENT_IDENTITY**: A purpose-built native IAM type that assigns unique, cryptographically attested SPIFFE IDs (`principal://agents.global.org...`) to reasoning engines.
*   **Access Control**: Simplifies IAM permissions. Instead of managing static credentials, the platform manages the identity lifecycle. Access tokens are scoped to the agent container.

## Configuration & Deployment
1.  **Deployment Script**:
    Add the `identity_type` parameter to the `_create_config` execution payload:
    ```python
    config = {
        "display_name": "pricing_assortment_orchestrator",
        "description": "Specialist pricing agent.",
        "agent_framework": "google-adk",
        "staging_bucket": "gs://your-staging-bucket",
        "identity_type": "AGENT_IDENTITY",  # Configure native Agent Identity
    }
    ```
2.  **SDK Client Registration**:
    Deploy using the Vertex AI / GenAI client SDK:
    ```python
    from vertexai.preview.reasoning_engines import ReasoningEngine
    
    engine = ReasoningEngine.create(
        reasoning_class=PricingAssortmentOrchestrator,
        config=config
    )
    ```

## Verification
*   Query the Vertex AI REST API to verify that the deployed resource contains:
    *   `"identityType": "AGENT_IDENTITY"`
    *   `"effectiveIdentity": "agents.global.org-.../reasoningEngines/...`
*   Verify sessions show up under **Sessions services** in the Google Cloud Console.
