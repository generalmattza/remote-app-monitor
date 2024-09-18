def format_text(
    text: str,
    fg_color: str = None,
    bg_color: str = None,
    bold: bool = False,
    dim: bool = False,
):
    # Given colors as strings such as "red", "green", "blue", etc.
    # Return coded text

    formatter = ANSITextFormatter(text, fg_color, bg_color, bold, dim)
    return formatter.format_text()


class ANSITextFormatter:
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

    def __init__(self, text, fg_color=None, bg_color=None, bold=False, dim=False):
        self.text = text
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
        return f"{ansi_code}{self.text}\033[0m"


# Example usage
if __name__ == "__main__":
    formatter = ANSITextFormatter(
        text="Hello, World!", fg_color="cyan", bg_color="magenta", bold=True
    )

    print(formatter.format_text())
