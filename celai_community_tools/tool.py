import functools
import inspect
from typing import Any, Callable, List, TypeVar, Union

from cel.assistants.common import Param
from cel.assistants.function_response import FunctionResponse
from celai_community_tools.auth import ToolAuthorization
from celai_community_tools.errors import ToolExecutionError

T = TypeVar("T")

def tool(
    func: Callable = None,
    desc: str = None,
    name: str = None,
    requires_auth: Union[ToolAuthorization, None] = None,
    requires_secrets: Union[List[str], None] = None,
    params: List[Param] = None,
) -> Callable:
    """
    A decorator that transforms a function into a Cel.ai tool.
    
    Args:
        func: The function to decorate.
        desc: Tool description. If not provided, uses the function's docstring.
        name: Tool name. If not provided, uses the function name.
        requires_auth: Authentication requirement for the tool.
        requires_secrets: List of secret keys required for the tool.
        params: List of parameters for the tool. If not provided, generates from function signature.
        
    Returns:
        The decorated function.
    """
    def decorator(func: Callable) -> Callable:
        func_name = str(getattr(func, "__name__", None))
        tool_name = name or func_name
        
        # Set tool metadata
        func.__tool_name__ = tool_name
        func.__tool_description__ = desc or inspect.cleandoc(func.__doc__ or "")
        func.__tool_requires_auth__ = requires_auth
        func.__tool_requires_secrets__ = requires_secrets
        
        # Generate params from function signature if not provided
        if params is None:
            func.__tool_params__ = _generate_params_from_signature(func)
        else:
            func.__tool_params__ = params
            
        # Handle async vs sync functions differently
        if inspect.iscoroutinefunction(func):
            @functools.wraps(func)
            async def func_with_error_handling(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await func(*args, **kwargs)
                except ToolExecutionError:
                    raise
                except Exception as e:
                    raise ToolExecutionError(
                        message=f"Error in execution of {tool_name}",
                        developer_message=f"Error in {func_name}: {e!s}",
                    ) from e
        else:
            @functools.wraps(func)
            def func_with_error_handling(*args: Any, **kwargs: Any) -> Any:
                try:
                    return func(*args, **kwargs)
                except ToolExecutionError:
                    raise
                except Exception as e:
                    raise ToolExecutionError(
                        message=f"Error in execution of {tool_name}",
                        developer_message=f"Error in {func_name}: {e!s}",
                    ) from e
                    
        # For Cel.ai compatibility, create the parameters list required for registration
        celai_params = []
        for param in func.__tool_params__:
            celai_params.append(
                Param(
                    name=param.name,
                    type=param.type,
                    description=param.description,
                    required=param.required,
                    enum=param.enum
                )
            )
            
        # Create the registration method for Cel.ai compatibility
        def register_with_celai(assistant):
            """Register this tool with a Cel.ai assistant."""
            assistant.function(
                name=tool_name,
                desc=func.__tool_description__,
                params=celai_params
            )(func_with_error_handling)
            
        func_with_error_handling.register_with_celai = register_with_celai
        
        return func_with_error_handling

    if func:
        return decorator(func)
    return decorator


def _generate_params_from_signature(func: Callable) -> List[Param]:
    """
    Generate parameter information from function signature.
    
    Args:
        func: The function to analyze.
        
    Returns:
        A list of Parameter objects.
    """
    from typing import get_type_hints
    
    signature = inspect.signature(func)
    type_hints = get_type_hints(func)
    
    # Skip context parameter which is typically the first parameter
    params = []
    for name, param in signature.parameters.items():
        # Skip self, ctx, context parameters
        if name in ['self', 'ctx', 'context', 'session']:
            continue
            
        # Get type information
        param_type = type_hints.get(name, Any)
        type_name = getattr(param_type, "__name__", str(param_type))
        
        # Convert Python types to string types
        type_map = {
            'str': 'string',
            'int': 'integer',
            'float': 'number',
            'bool': 'boolean',
            'list': 'array',
            'dict': 'object',
        }
        type_name = type_map.get(type_name, type_name.lower())
        
        # Check if parameter has a default value
        required = param.default == inspect.Parameter.empty
        
        # Try to extract description from docstring
        desc = f"Parameter {name}"
        if func.__doc__:
            import re
            pattern = rf"\s+{name}\s*:\s*(.*?)(?:\n\s+\w+\s*:|$)"
            match = re.search(pattern, func.__doc__, re.DOTALL)
            if match:
                desc = match.group(1).strip()
                
        params.append(Param(name=name, type=type_name, description=desc, required=required))
        
    return params


def deprecated(message: str) -> Callable:
    """
    Mark a tool as deprecated.
    
    Args:
        message: Deprecation message.
        
    Returns:
        Decorator function.
    """
    def decorator(func: Callable) -> Callable:
        func.__tool_deprecation_message__ = message
        return func

    return decorator

# Add deprecated method to tool for compatibility
tool.deprecated = deprecated