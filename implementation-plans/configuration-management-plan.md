# Configuration Management Plan

This document outlines the plan to externalize hardcoded parameters and implement a robust configuration management system for the application.

## 1. Identified Hardcoded Parameters

A review of the project files has identified a significant number of hardcoded parameters that should be externalized. These have been categorized by function:

### Credentials and API Keys:
*   **Odoo Credentials:** `odoo_url`, `odoo_db`, `odoo_login`, and `odoo_password` are hardcoded in both `config.py` and `odoo_functions.py`.
*   **Proxy URL:** The `proxy_url` in `config.py` contains credentials and should be stored securely.

### Service Configuration:
*   **Slack API Endpoints:** URLs for Slack APIs are hardcoded in `slack_integration.py`.
*   **Weaviate Pool Size:** The Weaviate connection pool is initialized with a hardcoded size and overflow in `lambda_function.py`.
*   **NLTK Data Path:** The path to NLTK data is hardcoded in `lambda_function.py`.
*   **Default Weather Location:** The `get_weather_data` function in `tools.py` defaults to "Fredericton".

### Application Logic and Behavior:
*   **User and Channel IDs:** A default `chat_id` and `user_id` are hardcoded for email processing in `lambda_function.py`.
*   **Mute Check User ID:** A specific user ID is hardcoded in the mute check logic in `lambda_function.py`.
*   **AI Model and Temperature:** The default AI temperature is set in `config.py`, and the default embedding model is specified in `lambda_function.py` and `tools.py`.
*   **Routing Logic:** The logic for selecting prompts and system behaviors based on `route_name` is hardcoded in `lambda_function.py`.
*   **User Agents:** The list of `USER_AGENTS` in `config.py` is static and could be managed dynamically.

### Database and Storage:
*   **DynamoDB Table Names:** Table names for DynamoDB are hardcoded in `config.py`.
*   **S3 Bucket Names:** S3 bucket names are hardcoded in `config.py`.

### Prompts and Templates:
*   **System Prompts:** All system prompts, instructions, and persona definitions are hardcoded in `prompts.py`. These could be managed in a database to allow for easier updates and A/B testing.

## 2. Proposed Configuration Management Plan

To address these issues, a two-part configuration management system is proposed:

1.  **Environment Variables for Secrets:** All sensitive information, such as API keys, passwords, and tokens, will be stored as environment variables.
2.  **Database for Dynamic Configuration:** A DynamoDB table will be used for non-sensitive parameters that may need to be updated without code changes.

### 2.1. Create a Configuration Database

A new table will be created in DynamoDB to store configuration parameters.

*   **TableName:** `ApplicationConfiguration`
*   **PrimaryKey:** `config_key` (String)
*   **Attributes:**
    *   `config_value` (String, Number, Boolean, or Map)
    *   `description` (String)
    *   `last_updated` (Timestamp)

### 2.2. Develop a Configuration Loader

A new function will be created to load all configurations at startup. This function will:
1.  Load secrets from environment variables.
2.  Fetch the remaining configuration parameters from the `ApplicationConfiguration` table in DynamoDB.
3.  Cache the configurations to avoid repeated database calls on every invocation.

### 2.3. Refactor the Application

The application code will be refactored to use the new configuration loader instead of hardcoded values.

### 2.4. Externalize Prompts

All prompts currently in `prompts.py` will be moved into the `ApplicationConfiguration` table.

### 2.5. Architecture Diagram

```mermaid
graph TD
    subgraph Application
        A[Lambda Function] --> B{Configuration Loader};
    end

    subgraph ConfigurationSources
        C[Environment Variables] --> B;
        D[DynamoDB: ApplicationConfiguration] --> B;
    end

    B --> E{Configuration Object};

    subgraph ApplicationModules
        F[odoo_functions.py] --> E;
        G[slack_integration.py] --> E;
        H[prompts.py] --> E;
        I[tools.py] --> E;
    end

    A --> F;
    A --> G;
    A --> H;
    A --> I;