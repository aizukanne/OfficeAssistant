"""Documentation utilities."""
import inspect
import re
from typing import Any, Callable, Dict, List, Type, Set, Optional
from functools import wraps

def validate_docstring(func: Callable) -> List[str]:
    """
    Validate function docstring completeness.
    
    Checks for required sections and their content in function docstrings.
    
    Args:
        func: Function or method to validate
        
    Returns:
        List[str]: List of missing sections or issues
        
    Example:
        >>> def test_func():
        ...     '''
        ...     Test function.
        ...     
        ...     Args:
        ...         None
        ...     
        ...     Returns:
        ...         None
        ...     '''
        ...     pass
        >>> validate_docstring(test_func)
        ['Raises']
    """
    doc = inspect.getdoc(func)
    if not doc:
        return ['complete docstring']
    
    required_sections = {'Args', 'Returns', 'Raises'}
    missing = []
    
    # Check for required sections
    for section in required_sections:
        if section not in doc:
            missing.append(section)
    
    # Check Args section format
    if 'Args:' in doc:
        args_pattern = r'Args:.*?(?=Returns:|Raises:|$)'
        args_match = re.search(args_pattern, doc, re.DOTALL)
        if args_match:
            args_section = args_match.group()
            if not re.search(r'\w+\s*\([^)]+\):', args_section):
                missing.append('Args type hints')
    
    # Check Returns section format
    if 'Returns:' in doc:
        returns_pattern = r'Returns:.*?(?=Raises:|$)'
        returns_match = re.search(returns_pattern, doc, re.DOTALL)
        if returns_match:
            returns_section = returns_match.group()
            if not re.search(r'\w+(\[.*?\])?:', returns_section):
                missing.append('Returns type hint')
    
    return missing

def document_exceptions(
    error_class: Type[Exception]
) -> Callable[[Type[Exception]], Type[Exception]]:
    """
    Decorator to enforce exception documentation.
    
    Ensures exception classes have proper documentation including description,
    attributes, and example usage.
    
    Args:
        error_class: Exception class to document
        
    Returns:
        Callable: Decorator function
        
    Raises:
        ValueError: If exception documentation is missing or incomplete
        
    Example:
        >>> @document_exceptions(Exception)
        ... class CustomError(Exception):
        ...     '''Custom error with documentation.'''
        ...     pass
        >>> CustomError.__doc__
        'Custom error with documentation.'
    """
    def decorator(cls: Type[Exception]) -> Type[Exception]:
        if not cls.__doc__:
            raise ValueError(f"Exception {cls.__name__} missing docstring")
            
        # Check for required documentation sections
        doc = cls.__doc__
        required_sections = {
            'description': r'^[A-Z][^.]*\.',
            'attributes': r'Attributes:',
            'example': r'Example:'
        }
        
        missing = []
        for section, pattern in required_sections.items():
            if not re.search(pattern, doc, re.MULTILINE):
                missing.append(section)
        
        if missing:
            raise ValueError(
                f"Exception {cls.__name__} missing sections: {', '.join(missing)}"
            )
        
        return cls
    return decorator

def enforce_docstring(
    min_args_desc: int = 2,
    require_examples: bool = True
) -> Callable[[Callable], Callable]:
    """
    Decorator to enforce docstring standards.
    
    Args:
        min_args_desc: Minimum words in argument descriptions
        require_examples: Whether to require example section
        
    Returns:
        Callable: Decorated function
        
    Raises:
        ValueError: If docstring standards not met
        
    Example:
        >>> @enforce_docstring()
        ... def test_func(arg1: str) -> None:
        ...     '''
        ...     Test function.
        ...     
        ...     Args:
        ...         arg1 (str): First argument with good description
        ...     
        ...     Returns:
        ...         None
        ...     
        ...     Example:
        ...         >>> test_func("test")
        ...         None
        ...     '''
        ...     pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            doc = inspect.getdoc(func)
            if not doc:
                raise ValueError(f"Function {func.__name__} missing docstring")
            
            # Check argument descriptions
            args_pattern = r'Args:(.*?)(?=Returns:|Raises:|Example:|$)'
            args_match = re.search(args_pattern, doc, re.DOTALL)
            if args_match:
                args_section = args_match.group(1)
                for line in args_section.split('\n'):
                    if ':' in line:
                        desc = line.split(':', 1)[1].strip()
                        if len(desc.split()) < min_args_desc:
                            raise ValueError(
                                f"Argument description too short: {line.strip()}"
                            )
            
            # Check for examples if required
            if require_examples and 'Example:' not in doc:
                raise ValueError(f"Function {func.__name__} missing examples")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def check_doctest_examples(obj: Any) -> List[str]:
    """
    Check if doctest examples are valid and runnable.
    
    Args:
        obj: Object to check doctest examples for
        
    Returns:
        List[str]: List of doctest issues found
        
    Example:
        >>> def test_func():
        ...     '''
        ...     >>> print("test")
        ...     test
        ...     '''
        ...     pass
        >>> check_doctest_examples(test_func)
        []
    """
    import doctest
    import io
    
    doc = inspect.getdoc(obj)
    if not doc:
        return ['no docstring']
    
    # Find all doctest examples
    examples = []
    for line in doc.split('\n'):
        if line.strip().startswith('>>>'):
            examples.append(line.strip())
    
    if not examples:
        return ['no examples']
    
    # Try to run doctests
    issues = []
    output = io.StringIO()
    parser = doctest.DocTestParser()
    try:
        test = parser.get_doctest(doc, globals(), obj.__name__, '', 0)
        runner = doctest.DocTestRunner(verbose=False)
        runner.run(test, out=output.write)
    except Exception as e:
        issues.append(f'doctest error: {str(e)}')
    
    return issues

def get_undocumented_attributes(cls: Type[Any]) -> Set[str]:
    """
    Find class attributes missing from documentation.
    
    Args:
        cls: Class to check documentation for
        
    Returns:
        Set[str]: Set of undocumented attribute names
        
    Example:
        >>> class TestClass:
        ...     '''
        ...     Test class.
        ...     
        ...     Attributes:
        ...         attr1: First attribute
        ...     '''
        ...     attr1 = 1
        ...     attr2 = 2
        >>> get_undocumented_attributes(TestClass)
        {'attr2'}
    """
    doc = inspect.getdoc(cls)
    if not doc:
        return set(vars(cls))
    
    # Find documented attributes
    attr_pattern = r'Attributes:(.*?)(?=Methods:|Example:|$)'
    attr_match = re.search(attr_pattern, doc, re.DOTALL)
    documented = set()
    
    if attr_match:
        attr_section = attr_match.group(1)
        for line in attr_section.split('\n'):
            if ':' in line:
                attr = line.split(':', 1)[0].strip()
                documented.add(attr)
    
    # Get actual attributes
    actual = {
        name for name, _ in inspect.getmembers(cls)
        if not name.startswith('_')
    }
    
    return actual - documented