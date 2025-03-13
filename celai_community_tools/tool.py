import functools
import inspect
from typing import Any, Callable, List, Optional, TypeVar, Union

from cel.assistants.common import Param
from cel.assistants.function_context import FunctionContext
from cel.assistants.function_response import FunctionResponse
from celai_community_tools.errors import ToolExecutionError

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
        
        # Generate params from function signature if not provided
        celai_params = params or _generate_params_from_signature(func)
        
        # Create a wrapper function in the format expected by Cel.ai
        @functools.wraps(func)
        async def celai_wrapper(session, params, ctx: FunctionContext):
            try:
                # Extract parameters from params dict for the original function
                kwargs = {}
                sig = inspect.signature(func)
                for param_name, param in sig.parameters.items():
                    if param_name == 'context' or param_name == 'ctx':
                        kwargs[param_name] = ctx
                    elif param_name in params:
                        kwargs[param_name] = params[param_name]
                
                # Call the original function
                if inspect.iscoroutinefunction(func):
                    result = await func(**kwargs)
                else:
                    result = func(**kwargs)
                
                # Handle different return types
                if isinstance(result, FunctionResponse):
                    return result
                elif isinstance(result, str):
                    return FunctionContext.response_text(result)
                else:
                    return FunctionContext.response_text(str(result))
                
            except Exception as e:
                error_message = f"Error in {tool_name}: {str(e)}"
                return FunctionContext.response_text(error_message)
        
        # Create the register_with_celai method
        def register_with_celai(assistant):
            """Register this tool with a Cel.ai assistant."""
            assistant.function(
                name=tool_name,
                desc=desc or inspect.cleandoc(func.__doc__ or ""),
                params=celai_params
            )(celai_wrapper)
            
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