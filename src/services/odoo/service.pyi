"""Type stubs for Odoo service."""
from typing import Dict, List, Any, Optional, Union
import xmlrpc.client
from src.interfaces import ServiceInterface

class OdooService(ServiceInterface):
    """Odoo service type hints."""
    
    common: xmlrpc.client.ServerProxy
    models: xmlrpc.client.ServerProxy
    db: str
    username: str
    password: str
    uid: int
    
    def __init__(self) -> None: ...
    
    def initialize(self) -> None: ...
    
    def validate_config(self) -> Dict[str, str]: ...
    
    def get_models(
        self,
        name_like: Optional[List[str]] = None
    ) -> List[str]: ...
    
    def get_fields(
        self,
        model_name: str
    ) -> Dict[str, Dict[str, Any]]: ...
    
    def create_record(
        self,
        model_name: str,
        data: Union[Dict[str, Any], List[Dict[str, Any]]],
        **kwargs: Any
    ) -> Union[int, List[int]]: ...
    
    def fetch_records(
        self,
        model_name: str,
        criteria: Optional[List] = None,
        limit: Optional[int] = None,
        fields_option: str = 'all',
        limited_fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]: ...
    
    def update_record(
        self,
        model_name: str,
        record_id: int,
        data: Dict[str, Any]
    ) -> bool: ...
    
    def delete_records(
        self,
        model_name: str,
        criteria: List
    ) -> bool: ...
    
    def print_record(
        self,
        model_name: str,
        record_id: int
    ) -> bytes: ...
    
    def execute_workflow(
        self,
        model_name: str,
        record_id: int,
        signal: str
    ) -> bool: ...