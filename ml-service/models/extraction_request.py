from pydantic import BaseModel
from typing import Any, TypeVar, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class ExtractionRequest(BaseModel):
    source_path: str
    """The absolute path to the source image file"""

    @staticmethod
    def from_dict(obj: Any) -> 'ExtractionRequest':
        assert isinstance(obj, dict)
        source_path = from_str(obj.get("source_path"))
        return ExtractionRequest(source_path)

    def to_dict(self) -> dict:
        result: dict = {}
        result["source_path"] = from_str(self.source_path)
        return result


def extraction_request_from_dict(s: Any) -> ExtractionRequest:
    return ExtractionRequest.from_dict(s)


def extraction_request_to_dict(x: ExtractionRequest) -> Any:
    return to_class(ExtractionRequest, x)
