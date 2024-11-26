import pytest
from app_monitor.text_formatter import TextFormat, TextFormatter, ANSITextFormatter


# Test cases for TextFormatter
@pytest.mark.parametrize(
    "text, width, precision, force_sign, padding, expected",
    [
        (123.456, 8, 2, False, " ", "  123.46"),  # Default padding (space)
        (123.456, 8, 2, True, " ", " +123.46"),  # Force sign
        (-123.456, 8, 2, True, " ", " -123.46"),  # Negative with sign
        (123.456, 8, 2, True, "0", "+0123.46"),  # Zero padding
        (-123.456, 8, 2, True, "0", "-0123.46"),  # Negative number with zero padding
        (123.456, 8, 2, False, "-", "--123.46"),  # Custom padding
        ("123.456", 10, 3, True, "0", "+00123.456"),  # String input with padding
        ("invalid", 8, 2, False, " ", "invalid"),  # Non-numeric string
    ],
)
def test_text_formatter(text, width, precision, force_sign, padding, expected):
    formatter = TextFormatter(
        text, width=width, precision=precision, force_sign=force_sign, padding=padding
    )
    assert formatter.format_text() == expected


# Test cases for ANSITextFormatter
@pytest.mark.parametrize(
    "text, fg_color, bg_color, bold, dim, width, precision, force_sign, padding, expected_text",
    [
        (
            123.456,
            "cyan",
            "magenta",
            True,
            False,
            8,
            2,
            False,
            " ",
            "\033[1;36;45m  123.46\033[0m",
        ),
        (
            123.456,
            "green",
            None,
            True,
            False,
            8,
            2,
            False,
            "0",
            "\033[1;32m00123.46\033[0m",
        ),
        (
            123.456,
            None,
            "red",
            False,
            True,
            8,
            2,
            False,
            "-",
            "\033[2;41m--123.46\033[0m",
        ),
        (
            123.456,
            "yellow",
            "blue",
            True,
            True,
            10,
            3,
            True,
            "*",
            "\033[1;2;33;44m+**123.456\033[0m",
        ),
    ],
)
def test_ansi_text_formatter(
    text,
    fg_color,
    bg_color,
    bold,
    dim,
    width,
    precision,
    force_sign,
    padding,
    expected_text,
):
    formatter = ANSITextFormatter(
        text=text,
        fg_color=fg_color,
        bg_color=bg_color,
        bold=bold,
        dim=dim,
        width=width,
        precision=precision,
        force_sign=force_sign,
        padding=padding,
    )
    assert formatter.format_text() == expected_text


# Test cases for TextFormat
@pytest.mark.parametrize(
    "text, config, expected",
    [
        # Without ANSI formatting
        (
            123.456,
            {
                "width": 8,
                "precision": 2,
                "force_sign": False,
                "ansi_enabled": False,
                "padding": " ",
            },
            "  123.46",
        ),
        (
            123.456,
            {
                "width": 8,
                "precision": 2,
                "force_sign": True,
                "ansi_enabled": False,
                "padding": "0",
            },
            "+0123.46",
        ),
        # With ANSI formatting
        (
            123.456,
            {
                "width": 8,
                "precision": 2,
                "force_sign": True,
                "ansi_enabled": True,
                "fg_color": "cyan",
                "bg_color": "magenta",
                "bold": True,
                "padding": "*",
            },
            "\033[1;36;45m+*123.46\033[0m",
        ),
    ],
)
def test_text_format(text, config, expected):
    format_obj = TextFormat(**config)
    assert format_obj.format_text(text) == expected


# Edge case tests
def test_text_formatter_edge_cases():
    # No width or precision
    formatter = TextFormatter(123.456)
    assert formatter.format_text() == "123.456"

    # Large numbers
    formatter = TextFormatter(1234567890.123456789, width=20, precision=4, padding="0")
    assert formatter.format_text() == "000001234567890.1235"

    # Small precision
    formatter = TextFormatter(123.456, width=10, precision=0, padding="*")
    assert formatter.format_text() == "*******123"

    # Non-numeric string
    formatter = TextFormatter("hello")
    assert formatter.format_text() == "hello"


def test_ansi_text_formatter_edge_cases():
    # No colors or styles
    formatter = ANSITextFormatter("Plain text")
    assert formatter.format_text() == "Plain text"

    # Invalid color names
    formatter = ANSITextFormatter("Text", fg_color="invalid", bg_color="invalid")
    assert formatter.format_text() == "Text"

    # Both bold and dim
    formatter = ANSITextFormatter("Bold and Dim", bold=True, dim=True)
    assert formatter.format_text() == "\033[1;2mBold and Dim\033[0m"

    # Custom padding with no styles
    formatter = ANSITextFormatter("Plain", padding="*")
    assert formatter.format_text() == "Plain"


if __name__ == "__main__":
    pytest.main()
