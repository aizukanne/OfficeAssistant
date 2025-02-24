"""Tests for documentation utilities."""
import pytest
from src.utils.docstring import (
    validate_docstring,
    document_exceptions,
    enforce_docstring,
    check_doctest_examples,
    get_undocumented_attributes
)

def test_validate_docstring_complete():
    """Test validation of complete docstring."""
    def test_func(arg1: str, arg2: int) -> str:
        """
        Test function with complete documentation.
        
        Args:
            arg1 (str): First argument
            arg2 (int): Second argument
            
        Returns:
            str: Result string
            
        Raises:
            ValueError: If arguments invalid
        """
        pass
    
    missing = validate_docstring(test_func)
    assert not missing, f"Found missing sections: {missing}"

def test_validate_docstring_missing_sections():
    """Test validation of incomplete docstring."""
    def test_func():
        """
        Test function with missing sections.
        
        Args:
            None
        """
        pass
    
    missing = validate_docstring(test_func)
    assert 'Returns' in missing
    assert 'Raises' in missing

def test_validate_docstring_no_doc():
    """Test validation of function without docstring."""
    def test_func():
        pass
    
    missing = validate_docstring(test_func)
    assert 'complete docstring' in missing

def test_document_exceptions_complete():
    """Test exception documentation decorator with complete doc."""
    @document_exceptions(Exception)
    class TestError(Exception):
        """
        Test error class.
        
        Attributes:
            message: Error message
            code: Error code
            
        Example:
            >>> raise TestError("test")
            TestError: test
        """
        pass
    
    assert TestError.__doc__ is not None

def test_document_exceptions_missing_doc():
    """Test exception documentation decorator with missing doc."""
    with pytest.raises(ValueError) as exc_info:
        @document_exceptions(Exception)
        class TestError(Exception):
            pass
    
    assert "missing docstring" in str(exc_info.value)

def test_document_exceptions_incomplete_doc():
    """Test exception documentation decorator with incomplete doc."""
    with pytest.raises(ValueError) as exc_info:
        @document_exceptions(Exception)
        class TestError(Exception):
            """Just a description."""
            pass
    
    assert "missing sections" in str(exc_info.value)

def test_enforce_docstring_complete():
    """Test docstring enforcement with complete doc."""
    @enforce_docstring()
    def test_func(arg1: str) -> None:
        """
        Test function with good documentation.
        
        Args:
            arg1 (str): First argument with detailed description
            
        Returns:
            None
            
        Example:
            >>> test_func("test")
            None
        """
        pass
    
    # Should not raise any exceptions
    test_func("test")

def test_enforce_docstring_short_desc():
    """Test docstring enforcement with short descriptions."""
    with pytest.raises(ValueError) as exc_info:
        @enforce_docstring(min_args_desc=3)
        def test_func(arg1: str) -> None:
            """
            Test function.
            
            Args:
                arg1 (str): Short
                
            Returns:
                None
                
            Example:
                >>> test_func("test")
                None
            """
            pass
    
    assert "description too short" in str(exc_info.value)

def test_enforce_docstring_missing_example():
    """Test docstring enforcement with missing example."""
    with pytest.raises(ValueError) as exc_info:
        @enforce_docstring(require_examples=True)
        def test_func(arg1: str) -> None:
            """
            Test function.
            
            Args:
                arg1 (str): First argument with good description
                
            Returns:
                None
            """
            pass
    
    assert "missing examples" in str(exc_info.value)

def test_check_doctest_examples_valid():
    """Test doctest checking with valid examples."""
    def test_func():
        """
        >>> print("test")
        test
        """
        pass
    
    issues = check_doctest_examples(test_func)
    assert not issues, f"Found issues: {issues}"

def test_check_doctest_examples_invalid():
    """Test doctest checking with invalid examples."""
    def test_func():
        """
        >>> print("test")
        wrong output
        """
        pass
    
    issues = check_doctest_examples(test_func)
    assert issues

def test_check_doctest_examples_no_examples():
    """Test doctest checking with no examples."""
    def test_func():
        """Test function without examples."""
        pass
    
    issues = check_doctest_examples(test_func)
    assert 'no examples' in issues

def test_get_undocumented_attributes_complete():
    """Test finding undocumented attributes with complete docs."""
    class TestClass:
        """
        Test class.
        
        Attributes:
            attr1: First attribute
            attr2: Second attribute
        """
        attr1 = 1
        attr2 = 2
    
    undocumented = get_undocumented_attributes(TestClass)
    assert not undocumented, f"Found undocumented attributes: {undocumented}"

def test_get_undocumented_attributes_missing():
    """Test finding undocumented attributes with missing docs."""
    class TestClass:
        """
        Test class.
        
        Attributes:
            attr1: First attribute
        """
        attr1 = 1
        attr2 = 2
        attr3 = 3
    
    undocumented = get_undocumented_attributes(TestClass)
    assert 'attr2' in undocumented
    assert 'attr3' in undocumented

def test_get_undocumented_attributes_no_doc():
    """Test finding undocumented attributes with no docs."""
    class TestClass:
        attr1 = 1
        attr2 = 2
    
    undocumented = get_undocumented_attributes(TestClass)
    assert 'attr1' in undocumented
    assert 'attr2' in undocumented

def test_docstring_inheritance():
    """Test docstring inheritance in class hierarchy."""
    class BaseClass:
        """
        Base class.
        
        Attributes:
            base_attr: Base attribute
        """
        base_attr = 1
    
    class ChildClass(BaseClass):
        """
        Child class.
        
        Attributes:
            child_attr: Child attribute
        """
        child_attr = 2
    
    undocumented = get_undocumented_attributes(ChildClass)
    assert not undocumented, f"Found undocumented attributes: {undocumented}"

def test_complex_docstring_validation():
    """Test validation of complex docstrings."""
    def test_func(
        arg1: str,
        arg2: int,
        *args: str,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Complex function with various parameters.
        
        Args:
            arg1 (str): First argument with detailed description
                that spans multiple lines and provides
                comprehensive documentation
            arg2 (int): Second argument that requires
                specific numeric values
            *args (str): Variable positional arguments
                for additional string processing
            **kwargs (Any): Variable keyword arguments
                for flexible configuration
                
        Returns:
            Dict[str, Any]: Result dictionary containing:
                - status (str): Operation status
                - data (Any): Processed data
                - metadata (Dict): Processing information
                
        Raises:
            ValueError: If arguments are invalid
                - arg1 must be non-empty
                - arg2 must be positive
            RuntimeError: If processing fails
                With detailed error context
                
        Example:
            >>> result = test_func("test", 42)
            >>> result['status']
            'success'
        """
        pass
    
    missing = validate_docstring(test_func)
    assert not missing, f"Found missing sections: {missing}"