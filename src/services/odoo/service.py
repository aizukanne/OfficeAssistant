"""Odoo service implementation."""
import os
from typing import Dict, List, Any, Optional, Union
import xmlrpc.client
from urllib.parse import urlparse

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    DatabaseError,
    OdooError,
    ConfigurationError
)
from src.utils.logging import log_message, log_error
from src.utils.decorators import log_function_call, log_error_decorator
from src.utils.error_handling import (
    handle_service_error,
    wrap_exceptions,
    retry_with_backoff
)
from src.interfaces import ServiceInterface

class OdooService(ServiceInterface):
    """Implementation of Odoo service interface."""
    
    def __init__(self) -> None:
        """Initialize the service."""
        self.initialize()
    
    def initialize(self) -> None:
        """Initialize Odoo client."""
        try:
            url = os.environ.get('ODOO_URL')
            if not url:
                raise ValidationError("Odoo URL is required")
                
            parsed = urlparse(url)
            self.common = xmlrpc.client.ServerProxy(f'{parsed.scheme}://{parsed.netloc}/xmlrpc/2/common')
            self.models = xmlrpc.client.ServerProxy(f'{parsed.scheme}://{parsed.netloc}/xmlrpc/2/object')
            
            # Authenticate and store uid
            self.db = os.environ.get('ODOO_DB')
            self.username = os.environ.get('ODOO_USERNAME')
            self.password = os.environ.get('ODOO_PASSWORD')
            
            self.uid = self.common.authenticate(
                self.db,
                self.username,
                self.password,
                {}
            )
            
            if not self.uid:
                raise AuthenticationError(
                    "Failed to authenticate with Odoo",
                    username=self.username,
                    db=self.db
                )
            
            log_message('INFO', 'odoo', 'Service initialized',
                       url=url, username=self.username)
                
        except Exception as e:
            handle_service_error(
                'odoo',
                'initialize',
                ConfigurationError,
                url_exists=bool(url),
                db_exists=bool(self.db),
                username_exists=bool(self.username)
            )(e)
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('ODOO_URL'):
            missing['ODOO_URL'] = "Odoo URL is required"
            log_message('ERROR', 'odoo', 'Missing Odoo URL')
        if not os.environ.get('ODOO_DB'):
            missing['ODOO_DB'] = "Odoo database name is required"
            log_message('ERROR', 'odoo', 'Missing Odoo database name')
        if not os.environ.get('ODOO_USERNAME'):
            missing['ODOO_USERNAME'] = "Odoo username is required"
            log_message('ERROR', 'odoo', 'Missing Odoo username')
        if not os.environ.get('ODOO_PASSWORD'):
            missing['ODOO_PASSWORD'] = "Odoo password is required"
            log_message('ERROR', 'odoo', 'Missing Odoo password')
            
        return missing

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='get_models')
    def get_models(
        self,
        name_like: Optional[List[str]] = None
    ) -> List[str]:
        """
        Get list of available models.
        
        Args:
            name_like: Optional list of substrings to filter model names
            
        Returns:
            List[str]: List of model names
            
        Raises:
            OdooError: If API request fails
        """
        try:
            domain = []
            if name_like:
                for pattern in name_like:
                    domain.append(('model', 'ilike', pattern))
            
            log_message('INFO', 'odoo', 'Getting models',
                       filters=name_like)
            
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'ir.model',
                'search_read',
                [domain],
                {'fields': ['model']}
            )
            
            log_message('INFO', 'odoo', 'Models retrieved',
                       count=len(result))
            return result
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'get_models',
                OdooError,
                filters=name_like
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='get_fields')
    def get_fields(
        self,
        model_name: str
    ) -> Dict[str, Dict[str, Any]]:
        """
        Get fields of a model.
        
        Args:
            model_name: Model name
            
        Returns:
            Dict[str, Dict[str, Any]]: Field definitions
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name:
                raise ValidationError("Model name is required")
            
            log_message('INFO', 'odoo', 'Getting fields',
                       model=model_name)
            
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'required', 'readonly', 'selection']}
            )
            
            log_message('INFO', 'odoo', 'Fields retrieved',
                       model=model_name, count=len(result))
            return result
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'get_fields',
                OdooError,
                model=model_name
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='create_record')
    def create_record(
        self,
        model_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any
    ) -> Union[int, List[int]]:
        """
        Create new record(s).
        
        Args:
            model_name: Model name
            data: Record data
            **kwargs: Additional parameters
            
        Returns:
            Union[int, List[int]]: Created record ID(s)
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name or not data:
                raise ValidationError(
                    "Missing required parameters",
                    model=bool(model_name),
                    data=bool(data)
                )
            
            log_message('INFO', 'odoo', 'Creating record(s)',
                       model=model_name,
                       is_batch=isinstance(data, list))
            
            if isinstance(data, list):
                result = self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'create',
                    [data]
                )
            else:
                result = self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'create',
                    [[data]]
                )[0]
            
            log_message('INFO', 'odoo', 'Record(s) created',
                       model=model_name,
                       record_ids=result)
            return result
                
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'create_record',
                OdooError,
                model=model_name,
                is_batch=isinstance(data, list)
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='fetch_records')
    def fetch_records(
        self,
        model_name: str,
        criteria: Optional[List] = None,
        limit: Optional[int] = None,
        fields_option: str = 'all',
        limited_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch records based on criteria.
        
        Args:
            model_name: Model name
            criteria: Search criteria
            limit: Maximum number of records
            fields_option: Fields to fetch ('all', 'limited')
            limited_fields: Specific fields to fetch
            
        Returns:
            List[Dict[str, Any]]: List of records
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name:
                raise ValidationError("Model name is required")
            
            domain = criteria or []
            options = {}
            
            if limit:
                options['limit'] = limit
            
            if fields_option == 'limited' and limited_fields:
                options['fields'] = limited_fields
            
            log_message('INFO', 'odoo', 'Fetching records',
                       model=model_name,
                       limit=limit,
                       fields_option=fields_option)
            
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'search_read',
                [domain],
                options
            )
            
            log_message('INFO', 'odoo', 'Records fetched',
                       model=model_name,
                       count=len(result))
            return result
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'fetch_records',
                OdooError,
                model=model_name,
                limit=limit
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='update_record')
    def update_record(
        self,
        model_name: str,
        record_id: int,
        data: Dict[str, Any]
    ) -> bool:
        """
        Update existing record.
        
        Args:
            model_name: Model name
            record_id: Record ID
            data: Update data
            
        Returns:
            bool: Success status
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name or not record_id or not data:
                raise ValidationError(
                    "Missing required parameters",
                    model=bool(model_name),
                    record_id=bool(record_id),
                    data=bool(data)
                )
            
            log_message('INFO', 'odoo', 'Updating record',
                       model=model_name,
                       record_id=record_id)
            
            self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'write',
                [[record_id], data]
            )
            
            log_message('INFO', 'odoo', 'Record updated',
                       model=model_name,
                       record_id=record_id)
            return True
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'update_record',
                OdooError,
                model=model_name,
                record_id=record_id
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='delete_records')
    def delete_records(
        self,
        model_name: str,
        criteria: List
    ) -> bool:
        """
        Delete records based on criteria.
        
        Args:
            model_name: Model name
            criteria: Deletion criteria
            
        Returns:
            bool: Success status
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name or not criteria:
                raise ValidationError(
                    "Missing required parameters",
                    model=bool(model_name),
                    criteria=bool(criteria)
                )
            
            log_message('INFO', 'odoo', 'Finding records to delete',
                       model=model_name)
            
            record_ids = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'search',
                [criteria]
            )
            
            if record_ids:
                log_message('INFO', 'odoo', 'Deleting records',
                           model=model_name,
                           count=len(record_ids))
                
                self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'unlink',
                    [record_ids]
                )
                
                log_message('INFO', 'odoo', 'Records deleted',
                           model=model_name,
                           count=len(record_ids))
            else:
                log_message('INFO', 'odoo', 'No records found to delete',
                           model=model_name)
            
            return True
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'delete_records',
                OdooError,
                model=model_name
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='print_record')
    def print_record(
        self,
        model_name: str,
        record_id: int
    ) -> bytes:
        """
        Print record as PDF.
        
        Args:
            model_name: Model name
            record_id: Record ID
            
        Returns:
            bytes: PDF content
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name or not record_id:
                raise ValidationError(
                    "Missing required parameters",
                    model=bool(model_name),
                    record_id=bool(record_id)
                )
            
            log_message('INFO', 'odoo', 'Generating PDF',
                       model=model_name,
                       record_id=record_id)
            
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'get_pdf',
                [[record_id]]
            )
            
            if not result:
                raise OdooError(
                    "Failed to generate PDF",
                    model=model_name,
                    record_id=record_id
                )
            
            log_message('INFO', 'odoo', 'PDF generated',
                       model=model_name,
                       record_id=record_id,
                       size=len(result))
            return result
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'print_record',
                OdooError,
                model=model_name,
                record_id=record_id
            )(e)

    @log_function_call('odoo')
    @retry_with_backoff(max_retries=3, exceptions=(xmlrpc.client.Fault,))
    @wrap_exceptions(OdooError, operation='execute_workflow')
    def execute_workflow(
        self,
        model_name: str,
        record_id: int,
        signal: str
    ) -> bool:
        """
        Execute workflow action.
        
        Args:
            model_name: Model name
            record_id: Record ID
            signal: Workflow signal
            
        Returns:
            bool: Success status
            
        Raises:
            OdooError: If API request fails
            ValidationError: If parameters are invalid
        """
        try:
            if not model_name or not record_id or not signal:
                raise ValidationError(
                    "Missing required parameters",
                    model=bool(model_name),
                    record_id=bool(record_id),
                    signal=bool(signal)
                )
            
            log_message('INFO', 'odoo', 'Executing workflow',
                       model=model_name,
                       record_id=record_id,
                       signal=signal)
            
            self.models.exec_workflow(
                self.db,
                self.uid,
                self.password,
                model_name,
                signal,
                record_id
            )
            
            log_message('INFO', 'odoo', 'Workflow executed',
                       model=model_name,
                       record_id=record_id,
                       signal=signal)
            return True
            
        except xmlrpc.client.Fault as e:
            handle_service_error(
                'odoo',
                'execute_workflow',
                OdooError,
                model=model_name,
                record_id=record_id,
                signal=signal
            )(e)