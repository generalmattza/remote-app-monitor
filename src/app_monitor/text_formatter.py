from dataclasses import dataclass
from typing import Any


# Apply padding to the formatted number
def get_length(value: Any):
    try:
        return len(value)
    except ValueError:
        return 0


@dataclass
class TextFormat:
    """
    Data class for specifying text formatting options.
    """

    width: int = None
    precision: int = None
    force_sign: bool = False
    ansi_enabled: bool = False
    fg_color: str = None
    bg_color: str = None
    bold: bool = False
    dim: bool = False
    padding: str = " "  # Default padding character is a space

    def format_text(self, text):
        """
        Format the given text using either ANSI or basic text formatting.

        Args:
            text: The text or number to format.

        Returns:
            str: The formatted text or number.
        """
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
                padding=self.padding,
            )
        else:
            formatter = TextFormatter(
                text,
                width=self.width,
                precision=self.precision,
                force_sign=self.force_sign,
                padding=self.padding,
            )
        return formatter.format_text()


class TextFormatter:
    """
    A class for basic text and number formatting.
    """

    def __init__(self, text, width=None, precision=None, force_sign=False, padding=" "):
        """
        Initialize the TextFormatter.

        Args:
            text: The text or number to format.
            width (int): Total width of the formatted string.
            precision (int): Decimal precision for numbers.
            force_sign (bool): Whether to force a sign on positive numbers.
            padding (str): Character to use for padding (default is space).
        """
        self.text = text
        self.width = width
        self.precision = precision
        self.force_sign = force_sign
        self.padding = padding

    def format_text(self):
        """
        Format the text or number according to the specified parameters.

        Returns:
            str: The formatted text or number.
        """
        # Attempt to convert text to a float if it's a string
        if isinstance(self.text, str):
            try:
                self.text = float(self.text)
            except ValueError:
                return self.text  # Return original text if it can't be converted

        # Format numbers with specified parameters
        if isinstance(self.text, (int, float)):
            sign_char = ""
            if self.force_sign or self.text < 0:
                sign_char = "+" if self.text >= 0 else "-"
                self.text = abs(
                    self.text
                )  # Work with the absolute value for formatting

            if self.precision is None:
                formatted_number = str(self.text)
            else:
                # Build the number formatting specification
                formatted_number = f"{self.text:.{self.precision}f}"

            sign_len = get_length(sign_char)
            num_len = get_length(formatted_number)
            if self.width is not None:
                if num_len + sign_len < self.width:
                    padding_length = self.width - num_len - sign_len
                    padding_str = self.padding * padding_length
                    # formatted_number = f"{sign_char}{padding_str}{formatted_number}"
                    if self.padding == " ":
                        # For zero padding, ensure the sign is at the start
                        formatted_number = f"{padding_str}{sign_char}{formatted_number}"
                    else:
                        # For other padding, apply after the sign
                        formatted_number = f"{sign_char}{padding_str}{formatted_number}"
            else:
                # If no padding is needed, just prepend the sign
                formatted_number = f"{sign_char}{formatted_number}"

            return formatted_number

        # Return non-numeric text as-is
        return str(self.text)


class ANSITextFormatter(TextFormatter):
    """
    A class for formatting text with ANSI color and style codes.
    """

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
        padding=" ",
    ):
        """
        Initialize the ANSITextFormatter.

        Args:
            text: The text or number to format.
            fg_color (str): Foreground color name.
            bg_color (str): Background color name.
            bold (bool): Apply bold text style.
            dim (bool): Apply dim text style.
        """
        super().__init__(
            text,
            width=width,
            precision=precision,
            force_sign=force_sign,
            padding=padding,
        )
        self.fg_color = fg_color
        self.bg_color = bg_color
        self.bold = bold
        self.dim = dim

    def _get_code(self, type_, color):
        """
        Get the ANSI color code for the foreground or background.

        Args:
            type_ (str): "fg" for foreground or "bg" for background.
            color (str): Color name.

        Returns:
            str: The ANSI color code.
        """
        if color is None:
            return ""
        color = color.lower()
        return self.COLORS.get(color, (None, None))[0 if type_ == "fg" else 1]

    def format_text(self):
        """
        Format the text with ANSI color and style codes.

        Returns:
            str: The formatted text with ANSI codes.
        """
        # Format the text using the base class method
        formatted_text = super().format_text()

        # Apply ANSI styling
        codes = []
        if self.bold:
            codes.append(self.STYLES["bold"])
        if self.dim:
            codes.append(self.STYLES["dim"])
        if self.fg_color:
            codes.append(self._get_code("fg", self.fg_color))
        if self.bg_color:
            codes.append(self._get_code("bg", self.bg_color))

        # Remove any None values from the codes list
        codes = [code for code in codes if code]
        # Construct the ANSI code string
        ansi_code = f"\033[{';'.join(codes)}m" if codes else ""
        exit_code = "\033[0m" if codes else ""
        return f"{ansi_code}{formatted_text}{exit_code}"


# Example usage
if __name__ == "__main__":
    formatter = ANSITextFormatter(
        text=123.456,
        fg_color="cyan",
        bg_color="magenta",
        bold=True,
        dim=False,
        width=10,
        precision=3,
        force_sign=True,
        padding="0",
    )
    print(formatter.format_text())
