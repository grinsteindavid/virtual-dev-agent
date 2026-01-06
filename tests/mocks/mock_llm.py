"""Fake LLM for unit tests."""

from langchain_core.messages import AIMessage


class FakeLLM:
    """Fake LLM for unit tests - no API calls."""
    
    def __init__(self, response: str = "Test response"):
        self.response = response
        self.calls = []
    
    def invoke(self, messages):
        """Synchronous invoke."""
        self.calls.append(messages)
        return AIMessage(content=self.response)
    
    async def ainvoke(self, messages):
        """Async invoke."""
        return self.invoke(messages)
    
    def bind_tools(self, tools):
        """Mock bind_tools - returns self."""
        return self
