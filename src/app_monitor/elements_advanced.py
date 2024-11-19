from dataclasses import asdict, dataclass
from typing import Mapping
from app_monitor.elements_base import MonitorElement, ProgressBar, Table, TextElement
from app_monitor.text_formatter import TextFormat


class UnpackMixin(Mapping):
    def __iter__(self):
        return iter(asdict(self).keys())

    def __len__(self):
        return len(asdict(self))

    def __getitem__(self, key):
        if key not in asdict(self):
            raise KeyError(f"Key {key} not found in {self.__class__.__name__}")
        return getattr(self, key)


class CoordinateTextElement(TextElement):
    def __init__(self, element_id, text, text_format=None, units=""):
        self.preamble = text
        self.units = units
        super().__init__(element_id=element_id, text=text, text_format=text_format)
        self.update(0, 0, 0)

    def update(self, x=None, y=None, z=None, units=None):
        self.x = x if x is not None else self.x or 0
        self.y = y if y is not None else self.y or 0
        self.z = z if z is not None else self.z or 0
        units = units or self.units

        self.text = (
            f"{self.preamble} "
            f"X: {self.x:+.4f} {units} "
            f"Y: {self.y:+.4f} {units} "
            f"Z: {self.z:+.4f} {units}"
        )


class ScaledTextElement(TextElement):
    def __init__(
        self, element_id, units="", static_text=None, scale=1, text_format=None
    ):
        super().__init__(
            element_id=element_id,
            text="",
            static_text=static_text,
            text_format=text_format,
        )
        self.scale = scale
        self.units = units

    def update(self, text):
        scaled_value = float(text) * self.scale
        return super().update(scaled_value)


@dataclass
class TextElementSettings(UnpackMixin):
    element_id: str
    text_format: TextFormat = None
    static_text: str = ""
    text: str = ""
    width: int = None
    _factory: TextElement = TextElement

    def build(self):
        return self._factory(
            element_id=self.element_id,
            text=self.text,
            static_text=self.static_text,
            text_format=self.text_format,
            width=self.width,
        )


@dataclass
class ScaledTextElementSettings(TextElementSettings):
    scale: float = 1
    units: str = ""

    _factory: ScaledTextElement = ScaledTextElement

    def build(self):
        return self._factory(
            element_id=self.element_id,
            units=self.units,
            static_text=self.static_text,
            scale=self.scale,
            text_format=self.text_format,
        )
