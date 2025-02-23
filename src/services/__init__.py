from .auth_service import authenticate

from .external_services import (
    get_coordinates,
    get_weather_data,
    calendar_operations,
    exchange_auth_code_for_tokens,
    browse_internet,
    google_search,
    clean_website_data
)

from .odoo_service import (
    get_models,
    get_fields,
    create_record,
    fetch_records,
    update_record,
    delete_records,
    print_record,
    fetch_data_from_api,
    get_database_schema
)

from .openai_service import (
    make_openai_api_call,
    make_openai_vision_call,
    make_openai_audio_call,
    ask_openai_o1,
    get_embedding,
    serialize_chat_completion_message
)

from .slack_service import (
    send_slack_message,
    send_audio_to_slack,
    send_file_to_slack,
    send_as_pdf,
    get_users,
    get_channels,
    manage_mute_status,
    upload_image_to_s3
)

from .storage_service import (
    save_message,
    get_last_messages,
    get_message_by_sort_id,
    get_messages_in_range,
    upload_to_s3,
    download_from_s3,
    delete_from_s3,
    list_s3_files,
    find_image_urls,
    decimal_default
)

__all__ = [
    # Auth Service
    'authenticate',
    
    # External Services
    'get_coordinates',
    'get_weather_data',
    'calendar_operations',
    'exchange_auth_code_for_tokens',
    'browse_internet',
    'google_search',
    'clean_website_data',
    
    # Odoo Service
    'get_models',
    'get_fields',
    'create_record',
    'fetch_records',
    'update_record',
    'delete_records',
    'print_record',
    'fetch_data_from_api',
    'get_database_schema',
    
    # OpenAI Service
    'make_openai_api_call',
    'make_openai_vision_call',
    'make_openai_audio_call',
    'ask_openai_o1',
    'get_embedding',
    'serialize_chat_completion_message',
    
    # Slack Service
    'send_slack_message',
    'send_audio_to_slack',
    'send_file_to_slack',
    'send_as_pdf',
    'get_users',
    'get_channels',
    'manage_mute_status',
    'upload_image_to_s3',
    
    # Storage Service
    'save_message',
    'get_last_messages',
    'get_message_by_sort_id',
    'get_messages_in_range',
    'upload_to_s3',
    'download_from_s3',
    'delete_from_s3',
    'list_s3_files',
    'find_image_urls',
    'decimal_default',
    'list_files'
]