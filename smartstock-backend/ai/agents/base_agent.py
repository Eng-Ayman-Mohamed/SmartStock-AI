from abc import ABC, abstractmethod

from pydantic import BaseModel

try:
    from langchain_core.tools import StructuredTool
except Exception:
    StructuredTool = None


class BaseTool(ABC):
    name: str
    description: str
    args_schema: type[BaseModel] | None = None

    @abstractmethod
    def run(self, input: dict) -> dict: ...

    def invoke(self, input: dict, config=None, **kwargs) -> dict:
        payload = input or {}
        if self.args_schema is not None:
            payload = self.args_schema(**payload).model_dump()
        return self.run(payload)

    def as_langchain_tool(self):
        if StructuredTool is None:
            raise ImportError('langchain-core StructuredTool is not available.')

        def _invoke(**kwargs):
            return self.invoke(kwargs)

        return StructuredTool.from_function(
            func=_invoke,
            name=self.name,
            description=self.description,
            args_schema=self.args_schema,
        )
