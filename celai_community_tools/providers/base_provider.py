from abc import ABCMeta
from typing import List

class ToolProviderMeta(ABCMeta):
    """Metaclass to auto-discover tools in provider classes."""
    def __new__(cls, name, bases, dct):
        new_class = super().__new__(cls, name, bases, dct)
        new_class._tools = []
        for attr in dct.values():
            if hasattr(attr, "_is_tool"):
                new_class._tools.append(attr)
        return new_class

class ToolProvider(metaclass=ToolProviderMeta):
    """Base class for tool providers to enable bulk registration."""
    
    @classmethod
    def get_tools(cls) -> List[callable]:
        """Return all tools marked with the @tool decorator."""
        return cls._tools
    
    @classmethod
    def register_tools(cls, assistant) -> None:
        """Register all tools in this provider with an assistant."""
        for tool in cls.get_tools():
            tool.register_with_celai(assistant)