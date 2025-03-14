import functools
import inspect
from typing import Callable, List, TypeVar

from cel.assistants.common import Param
from cel.assistants.function_response import FunctionResponse, RequestMode

T = TypeVar("T")

def tool(
    func: Callable = None,
    desc: str = None,
    name: str = None,
    requires_auth = None,
    requires_secrets = None,
    params: List[Param] = None,
) -> Callable:
    """
    A decorator that transforms a function into a Cel.ai compatible tool.
    
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
        tool_description = desc or inspect.cleandoc(func.__doc__ or "")
        
        # Generate params from function signature if not provided
        tool_params = params or _generate_params_from_signature(func)
        
        # Define a wrapper function that will be registered with Cel.ai
        # This needs to match Cel.ai's expected function signature
        @functools.wraps(func)
        async def celai_wrapper(session, params, ctx):
            try:
                # Call the original function with the params dict and ctx
                if inspect.iscoroutinefunction(func):
                    result = await func(params, ctx)
                else:
                    result = func(params, ctx)
                
                # If the result is already a FunctionResponse, return it directly
                if isinstance(result, FunctionResponse):
                    return result
                
                # Otherwise, wrap it in a FunctionResponse
                return FunctionResponse(
                    text=str(result),
                    request_mode=RequestMode.SINGLE
                )
            except Exception as e:
                # Log the error and return an error response
                error_msg = f"Error in {tool_name}: {str(e)}"
                return FunctionResponse(
                    text=error_msg,
                    request_mode=RequestMode.SINGLE
                )

        # Add the register_with_celai method to the wrapper
        def register_with_celai(assistant):
            """Register this tool with a Cel.ai assistant."""
            assistant.function(tool_name, tool_description, tool_params)(celai_wrapper)
            
        celai_wrapper.register_with_celai = register_with_celai
        
        return celai_wrapper

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
    signature = inspect.signature(func)
    
    # Skip the first parameter which is assumed to be the params dict
    # and the second parameter which is assumed to be the context
    params = []
    param_items = list(signature.parameters.items())
    
    # Skip the first two parameters (params and ctx)
    if len(param_items) >= 2:
        param_items = param_items[2:]
        
    for name, param in param_items:
        # Get type information
        param_type = param.annotation
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