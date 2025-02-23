import os
from typing import Dict, List, Any, Optional
import xmlrpc.client
from urllib.parse import urlparse

from src.config.settings import get_api_endpoint
from src.core.exceptions import (
    APIError,
    ValidationError,
    AuthenticationError,
    DatabaseError
)
from src.core.logging import ServiceLogger, log_function_call, log_error
from src.core.security import rate_limit, validate_request, audit_log
from src.core.performance import cached, monitor_performance
from src.services.interfaces import ServiceInterface

class OdooService(ServiceInterface):
    """Implementation of Odoo service interface."""
    
    def __init__(self):
        """Initialize the service."""
        self.logger = ServiceLogger('odoo_services')
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
                raise AuthenticationError("Failed to authenticate with Odoo")
                
        except Exception as e:
            self.logger.critical("Failed to initialize Odoo client", error=str(e))
            raise
    
    def validate_config(self) -> Dict[str, str]:
        """Validate service configuration."""
        missing = {}
        
        if not os.environ.get('ODOO_URL'):
            missing['ODOO_URL'] = "Odoo URL is required"
        if not os.environ.get('ODOO_DB'):
            missing['ODOO_DB'] = "Odoo database name is required"
        if not os.environ.get('ODOO_USERNAME'):
            missing['ODOO_USERNAME'] = "Odoo username is required"
        if not os.environ.get('ODOO_PASSWORD'):
            missing['ODOO_PASSWORD'] = "Odoo password is required"
            
        return missing

    @log_function_call(logger)
    @log_error(logger)
    @cached(ttl=3600)  # Cache for 1 hour
    @monitor_performance('odoo_get_models')
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
        """
        try:
            domain = []
            if name_like:
                for pattern in name_like:
                    domain.append(('model', 'ilike', pattern))
            
            return self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                'ir.model',
                'search_read',
                [domain],
                {'fields': ['model']}
            )
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @cached(ttl=3600)  # Cache for 1 hour
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'}
        },
        'required': ['model_name']
    })
    @monitor_performance('odoo_get_fields')
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
        """
        try:
            return self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'fields_get',
                [],
                {'attributes': ['string', 'type', 'required', 'readonly', 'selection']}
            )
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'},
            'data': {
                'type': ['object', 'array'],
                'items': {'type': 'object'}
            }
        },
        'required': ['model_name', 'data']
    })
    @audit_log('create_record')
    @monitor_performance('odoo_create_record')
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
        """
        try:
            if isinstance(data, list):
                return self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'create',
                    [data]
                )
            else:
                return self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'create',
                    [[data]]
                )[0]
                
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'},
            'criteria': {
                'type': ['object', 'array'],
                'items': {'type': 'object'}
            }
        },
        'required': ['model_name']
    })
    @monitor_performance('odoo_fetch_records')
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
        """
        try:
            domain = criteria or []
            options = {}
            
            if limit:
                options['limit'] = limit
            
            if fields_option == 'limited' and limited_fields:
                options['fields'] = limited_fields
            
            return self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'search_read',
                [domain],
                options
            )
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'},
            'record_id': {'type': 'integer'},
            'data': {'type': 'object'}
        },
        'required': ['model_name', 'record_id', 'data']
    })
    @audit_log('update_record')
    @monitor_performance('odoo_update_record')
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
        """
        try:
            self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'write',
                [[record_id], data]
            )
            return True
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'},
            'criteria': {'type': 'object'}
        },
        'required': ['model_name', 'criteria']
    })
    @audit_log('delete_records')
    @monitor_performance('odoo_delete_records')
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
        """
        try:
            record_ids = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'search',
                [criteria]
            )
            
            if record_ids:
                self.models.execute_kw(
                    self.db,
                    self.uid,
                    self.password,
                    model_name,
                    'unlink',
                    [record_ids]
                )
            
            return True
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @rate_limit(tokens=1)
    @validate_request({
        'type': 'object',
        'properties': {
            'model_name': {'type': 'string'},
            'record_id': {'type': 'integer'}
        },
        'required': ['model_name', 'record_id']
    })
    @monitor_performance('odoo_print_record')
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
        """
        try:
            result = self.models.execute_kw(
                self.db,
                self.uid,
                self.password,
                model_name,
                'get_pdf',
                [[record_id]]
            )
            
            if not result:
                raise APIError("Failed to generate PDF")
                
            return result
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")

    @log_function_call(logger)
    @log_error(logger)
    @monitor_performance('odoo_execute_workflow')
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
        """
        try:
            self.models.exec_workflow(
                self.db,
                self.uid,
                self.password,
                model_name,
                signal,
                record_id
            )
            return True
            
        except xmlrpc.client.Fault as e:
            self.logger.error("Odoo API error", error=str(e))
            raise APIError(f"Odoo API error: {str(e)}")