from cel.assistants.function_response import FunctionResponse
from cel.assistants.function_response import RequestMode


class ToolError(Exception):
    """Base class for all tool errors."""
    
    def __init__(self, message: str, developer_message: str = None):
        self.message = message
        self.developer_message = developer_message or message
        super().__init__(self.message)


class ToolExecutionError(ToolError):
    """Error raised when a tool execution fails."""
    
    def to_function_response(self) -> FunctionResponse:
        """Convert this error to a function response."""
        return FunctionResponse(
            text=f"Error: {self.message}",
            request_mode=RequestMode.SINGLE
        )


class RetryableToolError(ToolError):
    """Error raised when a tool execution fails but can be retried."""
    
    def __init__(self, message: str, developer_message: str = None, additional_prompt_content: str = None):
        super().__init__(message, developer_message)
        self.additional_prompt_content = additional_prompt_content or ""
        
    def to_function_response(self) -> FunctionResponse:
        """Convert this error to a function response."""
        return FunctionResponse(
            text=f"Error: {self.message}. Please try again with adjusted parameters.",
            request_mode=RequestMode.SINGLE
        )


class AuthorizationError(ToolError):
    """Error raised when tool authorization fails."""
    
    def to_function_response(self) -> FunctionResponse:
        """Convert this error to a function response."""
        return FunctionResponse(
            text=f"Authorization failed: {self.message}. Please check your credentials and try again.",
            request_mode=RequestMode.SINGLE
        )