from pydantic import BaseModel
from typing import Any, List, TypeVar, Callable, Type, cast


T = TypeVar("T")


def from_str(x: Any) -> str:
    assert isinstance(x, str)
    return x


def from_int(x: Any) -> int:
    assert isinstance(x, int) and not isinstance(x, bool)
    return x


def from_list(f: Callable[[Any], T], x: Any) -> List[T]:
    assert isinstance(x, list)
    return [f(y) for y in x]


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


class LocalizedCoordinate(BaseModel):
    height: int
    width: int
    x: int
    y: int

    @staticmethod
    def from_dict(obj: Any) -> 'LocalizedCoordinate':
        assert isinstance(obj, dict)
        height = from_int(obj.get("height"))
        width = from_int(obj.get("width"))
        x = from_int(obj.get("x"))
        y = from_int(obj.get("y"))
        return LocalizedCoordinate(height, width, x, y)

    def to_dict(self) -> dict:
        result: dict = {}
        result["height"] = from_int(self.height)
        result["width"] = from_int(self.width)
        result["x"] = from_int(self.x)
        result["y"] = from_int(self.y)
        return result


class ExtractionMetadataResponse(BaseModel):
    bboxes: List[List[int]]
    hardware_mode_used: str
    layers_extracted: int
    localized_coordinates: List[LocalizedCoordinate]
    message: str
    output_paths: List[str]
    source_path: str
    status: str

    @staticmethod
    def from_dict(obj: Any) -> 'ExtractionMetadataResponse':
        assert isinstance(obj, dict)
        bboxes = from_list(lambda x: from_list(from_int, x), obj.get("bboxes"))
        hardware_mode_used = from_str(obj.get("hardware_mode_used"))
        layers_extracted = from_int(obj.get("layers_extracted"))
        localized_coordinates = from_list(LocalizedCoordinate.from_dict, obj.get("localized_coordinates"))
        message = from_str(obj.get("message"))
        output_paths = from_list(from_str, obj.get("output_paths"))
        source_path = from_str(obj.get("source_path"))
        status = from_str(obj.get("status"))
        return ExtractionMetadataResponse(bboxes, hardware_mode_used, layers_extracted, localized_coordinates, message, output_paths, source_path, status)

    def to_dict(self) -> dict:
        result: dict = {}
        result["bboxes"] = from_list(lambda x: from_list(from_int, x), self.bboxes)
        result["hardware_mode_used"] = from_str(self.hardware_mode_used)
        result["layers_extracted"] = from_int(self.layers_extracted)
        result["localized_coordinates"] = from_list(lambda x: to_class(LocalizedCoordinate, x), self.localized_coordinates)
        result["message"] = from_str(self.message)
        result["output_paths"] = from_list(from_str, self.output_paths)
        result["source_path"] = from_str(self.source_path)
        result["status"] = from_str(self.status)
        return result


def extraction_request_from_dict(s: Any) -> ExtractionRequest:
    return ExtractionRequest.from_dict(s)


def extraction_request_to_dict(x: ExtractionRequest) -> Any:
    return to_class(ExtractionRequest, x)


def extraction_metadata_response_from_dict(s: Any) -> ExtractionMetadataResponse:
    return ExtractionMetadataResponse.from_dict(s)


def extraction_metadata_response_to_dict(x: ExtractionMetadataResponse) -> Any:
    return to_class(ExtractionMetadataResponse, x)
