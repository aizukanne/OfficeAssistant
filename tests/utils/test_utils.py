"""Test utilities for standardized testing."""
import pytest
import asyncio
import inspect
from typing import Any, Callable, Dict, List, Type, Optional, Union
from unittest.mock import MagicMock, patch

def create_service_mock(
    service_class: Type[Any],
    **method_returns: Any
) -> MagicMock:
    """
    Create a standardized service mock.
    
    Args:
        service_class: Service class to mock
        **method_returns: Return values for specific methods
        
    Returns:
        MagicMock: Configured service mock
        
    Example:
        >>> mock = create_service_mock(StorageService, upload_to_s3='s3://url')
        >>> mock.upload_to_s3()
        's3://url'
    """
    mock = MagicMock(spec=service_class)
    for method, return_value in method_returns.items():
        setattr(mock, method, MagicMock(return_value=return_value))
    return mock

def async_test(coro: Callable) -> Callable:
    """
    Decorator for async test functions.
    
    Args:
        coro: Async function to wrap
        
    Returns:
        Callable: Wrapped function
        
    Example:
        >>> @async_test
        ... async def test_async():
        ...     return 'result'
        >>> test_async()
        'result'
    """
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return asyncio.run(coro(*args, **kwargs))
    return wrapper

def create_aws_mock(**service_configs: Dict[str, Any]) -> MagicMock:
    """
    Create standardized AWS service mocks.
    
    Args:
        **service_configs: Configuration for each service
        
    Returns:
        MagicMock: Configured AWS mock
        
    Example:
        >>> mock = create_aws_mock(
        ...     s3={'bucket': 'test-bucket'},
        ...     dynamodb={'table': 'test-table'}
        ... )
    """
    mock = MagicMock()
    
    # Configure S3 mock
    if 's3' in service_configs:
        s3_config = service_configs['s3']
        s3_mock = MagicMock()
        s3_mock.upload_fileobj.return_value = None
        s3_mock.download_fileobj.return_value = None
        s3_mock.delete_object.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock.client.return_value = s3_mock
    
    # Configure DynamoDB mock
    if 'dynamodb' in service_configs:
        dynamodb_config = service_configs['dynamodb']
        table_mock = MagicMock()
        table_mock.put_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        table_mock.get_item.return_value = {'Item': {'id': 'test'}}
        table_mock.delete_item.return_value = {'ResponseMetadata': {'HTTPStatusCode': 200}}
        mock.Table.return_value = table_mock
    
    return mock

def create_http_mock(
    responses: Dict[str, Any],
    status_codes: Optional[Dict[str, int]] = None
) -> MagicMock:
    """
    Create standardized HTTP client mock.
    
    Args:
        responses: Response data for different endpoints
        status_codes: Status codes for different endpoints
        
    Returns:
        MagicMock: Configured HTTP mock
        
    Example:
        >>> mock = create_http_mock(
        ...     responses={'/api/test': {'data': 'test'}},
        ...     status_codes={'/api/test': 200}
        ... )
    """
    mock = MagicMock()
    status_codes = status_codes or {k: 200 for k in responses}
    
    def mock_request(method: str, url: str, *args: Any, **kwargs: Any) -> MagicMock:
        response = MagicMock()
        response.status_code = status_codes.get(url, 200)
        response.json.return_value = responses.get(url, {})
        return response
    
    mock.request.side_effect = mock_request
    return mock

def validate_mock_calls(
    mock: MagicMock,
    expected_calls: List[Dict[str, Any]]
) -> List[str]:
    """
    Validate mock was called as expected.
    
    Args:
        mock: Mock to validate
        expected_calls: List of expected calls with args/kwargs
        
    Returns:
        List[str]: List of validation errors
        
    Example:
        >>> mock = MagicMock()
        >>> mock.test(1, key='value')
        >>> errors = validate_mock_calls(mock, [
        ...     {'method': 'test', 'args': (1,), 'kwargs': {'key': 'value'}}
        ... ])
        >>> assert not errors
    """
    errors = []
    
    for expected in expected_calls:
        method = expected['method']
        args = expected.get('args', ())
        kwargs = expected.get('kwargs', {})
        
        mock_method = getattr(mock, method)
        if not mock_method.called:
            errors.append(f"Method {method} was not called")
            continue
            
        actual_calls = mock_method.call_args_list
        matching_call = any(
            call[0] == args and call[1] == kwargs
            for call in actual_calls
        )
        
        if not matching_call:
            errors.append(
                f"Method {method} was not called with args={args}, kwargs={kwargs}"
            )
    
    return errors

def create_response_mock(
    data: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> MagicMock:
    """
    Create standardized response mock.
    
    Args:
        data: Response data
        status_code: HTTP status code
        headers: Response headers
        
    Returns:
        MagicMock: Configured response mock
        
    Example:
        >>> mock = create_response_mock({'key': 'value'}, 200)
        >>> assert mock.json()['key'] == 'value'
    """
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    mock.headers = headers or {}
    return mock

def patch_service(
    service_name: str,
    **configs: Any
) -> Callable:
    """
    Decorator to patch service dependencies.
    
    Args:
        service_name: Name of service to patch
        **configs: Configuration for different dependencies
        
    Returns:
        Callable: Decorator function
        
    Example:
        >>> @patch_service('storage', s3={'bucket': 'test'})
        ... def test_function(mock_service):
        ...     return mock_service.s3_client
    """
    def decorator(func: Callable) -> Callable:
        # Determine patches based on service
        patches = []
        if 's3' in configs:
            patches.append(
                patch('boto3.client', return_value=create_aws_mock(**configs)['s3'])
            )
        if 'dynamodb' in configs:
            patches.append(
                patch('boto3.resource', return_value=create_aws_mock(**configs)['dynamodb'])
            )
        if 'http' in configs:
            patches.append(
                patch('requests.Session', return_value=create_http_mock(**configs['http']))
            )
        
        # Apply all patches
        for p in patches:
            func = p(func)
        return func
    
    return decorator