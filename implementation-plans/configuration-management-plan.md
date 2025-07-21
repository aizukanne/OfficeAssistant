# Configuration Management Plan (Multi-Tenant Architecture)

This document outlines the plan to externalize hardcoded parameters and implement a robust, multi-tenant configuration management system for the application.

## 1. Overview

The initial plan has been revised to support a multi-tenant architecture, allowing different companies to use and customize the application independently. This requires a clear distinction between global settings and tenant-specific configurations that can be managed by each company.

## 2. Configuration Tiers

We will implement two tiers of configuration:

*   **Global Configuration:** Core application settings and default values that are consistent across all tenants.
*   **Tenant-Specific Configuration:** Parameters that can be customized by each company. These settings will override any global defaults.

## 3. Tenant-Specific Configurable Parameters

The following parameters have been identified as candidates for tenant-specific configuration:

### Credentials & API Keys (Managed as Secrets)
*   Odoo Credentials (`odoo_url`, `odoo_db`, `odoo_login`, `odoo_password`)
*   Slack Bot Token (`slack_bot_token`)
*   Telegram Bot Token (`telegram_bot_token`)
*   ERPNext Credentials (`erpnext_api_key`, `erpnext_api_secret`)
*   Google API Key & Calendar ID (`google_api_key`, `calendar_id`)
*   Weaviate Credentials (`weaviate_api_key`, `weaviate_url`)
*   API keys for AI models (OpenAI, OpenRouter, Cerebras)

### Branding and Persona
*   **AI Persona:** The AI's name, persona description, and communication style (from `prompts.py`).
*   **Company Information:** Details about the tenant's company to be used in system prompts.

### Application Behavior
*   **System Prompts:** All instructional and system prompts from `prompts.py`.
*   **Default AI Parameters:** Default temperature, model selection for different tasks (e.g., `chitchat` vs. `writing`).
*   **Routing Logic:** The mapping of intent routes to specific prompt configurations.
*   **Email Notification Settings:** The Slack channel (`chat_id`) and user (`user_id`) for email notifications.

### Data Storage
*   **S3 Bucket Names:** Tenant-specific bucket names for data isolation.
*   **DynamoDB Table Naming:** A prefix for all DynamoDB tables to isolate data per tenant.

## 4. Implementation Strategy

### 4.1. Secrets Management
All secrets will be stored in **AWS Secrets Manager**. A unique secret will be created for each tenant, following a consistent naming convention (e.g., `production/tenant/<tenant_id>`).

### 4.2. Tenant Configuration Database
A new DynamoDB table will be created to store tenant-level configurations.

*   **TableName:** `TenantConfiguration`
*   **Partition Key:** `tenant_id` (String)
*   **Sort Key:** `config_key` (String)
*   **Attributes:**
    *   `config_value` (String, Number, Boolean, or Map)
    *   `description` (String)

### 4.3. Enhanced Configuration Loader
The application's entry point (`lambda_function.py`) will be updated to:
1.  Identify the `tenant_id` from every incoming request.
2.  Invoke an enhanced `ConfigurationLoader` with the `tenant_id`.
3.  The loader will:
    a.  Fetch tenant-specific secrets from AWS Secrets Manager.
    b.  Fetch all configuration parameters for the `tenant_id` from the `TenantConfiguration` table.
    c.  Load any global default configurations as a fallback.
    d.  Merge the configurations, with tenant-specific values taking precedence.
    e.  Return a comprehensive configuration object to be used for the duration of the request.

## 5. Revised Architecture Diagram

```mermaid
graph TD
    subgraph "Incoming Request"
        A[Event with tenant_id] --> B[Lambda Function];
    end

    subgraph "Configuration Loading"
        B -- "1. Get tenant_id" --> C{Configuration Loader};
        C -- "2. Fetch Secrets" --> D[AWS Secrets Manager];
        C -- "3. Fetch Config" --> E[DynamoDB: TenantConfiguration];
        D -- "Tenant Secrets" --> C;
        E -- "Tenant-specific Params" --> C;
        C -- "4. Merged Config" --> F{Configuration Object};
    end

    subgraph "Application Logic"
        B -- "Uses" --> F;
        G[Application Modules] -- "Uses" --> F;
        B --> G;
    end