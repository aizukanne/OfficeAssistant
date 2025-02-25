# Lambda Function Refactoring Plan

## Proposed Module Organization

### 1. Core API Handler (lambda_handler.py)
- `lambda_handler`: Main entry point
- Core event processing logic
- Route handling

### 2. OpenAI Integration (openai_client.py)
- `make_openai_api_call`
- `make_openai_vision_call`
- `make_openai_audio_call`
- `ask_openai_o1`
- `get_embedding`
- `text_to_speech`
- `transcribe_speech_from_memory`
- `transcribe_multiple_urls`

### 3. Conversation Management (conversation_builder.py)
- `make_text_conversation`
- `make_vision_conversation`
- `make_audio_conversation`
- `handle_message_content`
- `handle_tool_calls`
- `serialize_chat_completion_message`

### 4. Database Operations (db_operations.py)
- `save_message`
- `get_last_messages`
- `get_message_by_sort_id`
- `get_messages_in_range`
- `decimal_default`
- `convert_floats_to_decimals`

### 5. User Management (user_management.py)
- `get_users`
- `update_slack_users`
- `get_slack_user_name`
- `smart_send_message`

### 6. Channel Management (channel_management.py)
- `get_channels`
- `update_slack_conversations`
- `manage_mute_status`

### 7. Message Processing (message_processing.py)
- `load_stopwords`
- `rank_sentences`
- `summarize_record`
- `summarize_messages`
- `clean_website_data`

### 8. Slack Integration (slack_client.py)
- `send_slack_message`
- `send_audio_to_slack`
- `send_file_to_slack`
- `convert_markdown_to_slack`
- `convert_to_slack_blocks`
- `latex_to_slack`

### 9. File Operations (file_operations.py)
- `download_and_read_file`
- `upload_document_to_s3`
- `upload_image_to_s3`
- `list_files`
- `send_as_pdf`
- Class: `MyFPDF`

### 10. Web Services (web_services.py)
- `browse_internet`
- `google_search`
- `get_web_pages`
- `fetch_page`
- `process_page`

### 11. Audio Processing (audio_processing.py)
- `download_audio_to_memory`
- `process_url`
- `convert_to_wav_in_memory`

### 12. Utility Functions (utils.py)
- `normalize_message`
- `replace_problematic_chars`
- `solve_maths`
- `is_serializable`
- `find_image_urls`
- `message_to_json`

### 13. Configuration (config.py)
- Environment variables
- API keys and credentials
- Constants and default values
- DynamoDB table names
- S3 bucket names
- User agents list

### 14. Error Handling (error_handlers.py)
- Custom exception classes
- Error logging configuration
- Error response formatting
- Error code definitions

### 15. Middleware (middleware.py)
- Request validation
- Authentication/Authorization checks
- Logging middleware
- Rate limiting
- Request/Response transformation

## Project Structure
```
/src
  /handlers
    lambda_handler.py
  /clients
    openai_client.py
    slack_client.py
  /services
    conversation_builder.py
    message_processing.py
    web_services.py
    audio_processing.py
  /data
    db_operations.py
    user_management.py
    channel_management.py
  /utils
    file_operations.py
    utils.py
  /core
    config.py
    error_handlers.py
    middleware.py
/tests
  /unit
    /handlers
    /clients
    /services
    /data
    /utils
    /core
  /integration
  /e2e
/docs
  /api
  /architecture
  /deployment
```

## Benefits of This Organization

1. **Improved Maintainability**: 
   - Each module has a single responsibility
   - Clear separation of concerns
   - Easy to locate and modify specific functionality

2. **Better Testing**: 
   - Modules can be tested independently
   - Clear boundaries for unit tests
   - Easier to mock dependencies

3. **Easier Collaboration**: 
   - Team members can work on different modules
   - Reduced merge conflicts
   - Clear ownership of components

4. **Code Reusability**: 
   - Functions are grouped logically
   - Common utilities are centralized
   - Consistent patterns across modules

5. **Enhanced Security**:
   - Centralized configuration management
   - Consistent error handling
   - Proper separation of sensitive data

## Implementation Strategy

1. **Phase 1: Setup**
   - Create new directory structure
   - Set up testing framework
   - Configure linting and formatting
   - Set up CI/CD pipeline

2. **Phase 2: Core Infrastructure**
   - Implement config.py
   - Set up error handling
   - Create middleware framework
   - Establish logging

3. **Phase 3: Module Migration**
   - Move functions to new modules one at a time
   - Update imports and dependencies
   - Add tests for each module
   - Document each module

4. **Phase 4: Testing & Validation**
   - Write unit tests
   - Add integration tests
   - Perform end-to-end testing
   - Validate error handling

5. **Phase 5: Documentation & Cleanup**
   - Update API documentation
   - Add architecture diagrams
   - Clean up deprecated code
   - Review security considerations

## Questions for Discussion

1. Should we split any of these modules further?
2. Are there any functions that should be moved to different modules?
3. How should we handle cross-cutting concerns?
4. What testing strategy should we adopt?
5. How should we handle versioning and backwards compatibility?

## Next Steps

1. Review and agree on module organization
2. Create detailed implementation plan for each phase
3. Set up development environment and tools
4. Begin incremental implementation
5. Establish review process for each phase