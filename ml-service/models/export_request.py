from enum import Enum
from pydantic import BaseModel
from typing import List, Any, TypeVar, Callable, Type, cast


T = TypeVar("T")
EnumT = TypeVar("EnumT", bound=Enum)


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


def to_enum(c: Type[EnumT], x: Any) -> EnumT:
    assert isinstance(x, c)
    return x.value


def to_class(c: Type[T], x: Any) -> dict:
    assert isinstance(x, c)
    return cast(Any, x).to_dict()


class Format(Enum):
    PNG = "PNG"
    PSD = "PSD"
    SVG = "SVG"
    TIFF_CMYK = "TIFF_CMYK"
    TIFF_RGB = "TIFF_RGB"


class ExportRequest(BaseModel):
    destination_folder: str
    """The absolute path to the destination folder chosen by the user"""

    formats: List[Format]
    """An array of requested export formats"""

    @staticmethod
    def from_dict(obj: Any) -> 'ExportRequest':
        assert isinstance(obj, dict)
        destination_folder = from_str(obj.get("destination_folder"))
        formats = from_list(Format, obj.get("formats"))
        return ExportRequest(destination_folder, formats)

    def to_dict(self) -> dict:
        result: dict = {}
        result["destination_folder"] = from_str(self.destination_folder)
        result["formats"] = from_list(lambda x: to_enum(Format, x), self.formats)
        return result


def export_request_from_dict(s: Any) -> ExportRequest:
    return ExportRequest.from_dict(s)


def export_request_to_dict(x: ExportRequest) -> Any:
    return to_class(ExportRequest, x)
