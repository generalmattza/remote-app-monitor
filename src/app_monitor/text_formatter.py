from dataclasses import dataclass


@dataclass
class TextFormat:
    width: int = None
    precision: int = None
    force_sign: bool = False
    ansi_enabled: bool = False
    fg_color: str = None
    bg_color: str = None
    bold: bool = False
    dim: bool = False

    def format_text(self, text):
        if self.ansi_enabled:
            formatter = ANSITextFormatter(
                text,
                fg_color=self.fg_color,
                bg_color=self.bg_color,
                bold=self.bold,
                dim=self.dim,
                width=self.width,
                precision=self.precision,
                force_sign=self.force_sign,
            )
        else:
            formatter = TextFormatter(
                text,
                width=self.width,
                precision=self.precision,
                force_sign=self.force_sign,
            )
        return formatter.format_text()


class TextFormatter:
    def __init__(self, text, width=None, precision=None, force_sign=False):
        self.text = text
        self.width = width
        self.precision = precision
        self.force_sign = force_sign

    def format_text(self):
        # Format the number if width, precision, or force_sign is specified
        if isinstance(self.text, str):
            try:
                self.text = float(self.text)
            except ValueError:
                return self.text
        if isinstance(self.text, (int, float)):
            # Build the format specification string
            sign = "+" if self.force_sign else ""
            format_spec = (
                f"{sign}{self.width}.{self.precision}f"
                if self.precision is not None
                else f"{self.width}f"
            )
            # Format the text according to the specification
            return f"{float(self.text):{format_spec}}"
        else:
            # If it's not a number, return as-is
            return str(self.text)


class ANSITextFormatter(TextFormatter):
    COLORS = {
        "black": ("30", "40"),
        "red": ("31", "41"),
        "green": ("32", "42"),
        "yellow": ("33", "43"),
        "blue": ("34", "44"),
        "magenta": ("35", "45"),
        "cyan": ("36", "46"),
        "white": ("37", "47"),
    }

    STYLES = {"bold": "1", "dim": "2"}

    def __init__(
        self,
        text,
        fg_color=None,
        bg_color=None,
        bold=False,
        dim=False,
        width=None,
        precision=None,
        force_sign=False,
    ):
        super().__init__(text, width=width, precision=precision, force_sign=force_sign)
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.bold = bold
        self.dim = dim

    def _get_code(self, type_, color):
        if color is None:
            return ""
        color = color.lower()
        return self.COLORS.get(color, (None, None))[0 if type_ == "fg" else 1]

    def format_text(self):
        # First, format the text using the base class's method
        formatted_text = super().format_text()

        # Apply ANSI formatting if enabled
        codes = []
        if self.bold:
            codes.append(self.STYLES["bold"])
        if self.dim:
            codes.append(self.STYLES["dim"])
        if self.fg_color:
            codes.append(self._get_code("fg", self.fg_color))
        if self.bg_color:
            codes.append(self._get_code("bg", self.bg_color))

        ansi_code = f"\033[{';'.join(codes)}m" if codes else ""
        return f"{ansi_code}{formatted_text}\033[0m"


# Example usage
if __name__ == "__main__":
    formatter = ANSITextFormatter(
        text=123.456,
        fg_color="cyan",
        bg_color="magenta",
        bold=True,
        width=8,
        precision=2,
    )
    print(formatter.format_text())
