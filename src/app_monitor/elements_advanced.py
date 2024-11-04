from app_monitor.elements_base import MonitorElement, ProgressBar, Table, TextElement


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
