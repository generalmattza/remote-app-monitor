import pytest
from app_monitor.elements_base import (
    MonitorElement,
    MonitorGroup,
    TextElement,
    ProgressBar,
    RangeBar,
    Table,
    LogMonitor,
    IndicatorLamp,
)

from app_monitor.elements_advanced import MachineState


def test_monitor_element_initialization():
    element = MonitorElement(border=True, width=50)
    assert element.border is True
    assert element.width == 50
    assert isinstance(element.element_id, str)


def test_monitor_element_add_border():
    element = MonitorElement(border=True, width=30)
    content = "Test Content"
    bordered_content = element.add_border(content)
    assert bordered_content.startswith("+")
    assert bordered_content.endswith("+")
    assert "| Test Content |" in bordered_content


def test_text_element_update_and_display():
    text = TextElement(static_text="Static: ", text="Initial")
    assert text.display() == "Static: Initial"
    text.update("Updated")
    assert text.display() == "Static: Updated"


def test_progress_bar_update_and_display():
    progress = ProgressBar(total_steps=10, label="Loading")
    progress.update(5)
    display = progress.display()
    assert "Loading" in display
    assert "█" in display
    assert "░" in display
    assert "50.0%" in display


def test_range_bar_update_and_display():
    range_bar = RangeBar(min_value=0, max_value=100, label="Range")
    range_bar.update(50)
    display = range_bar.display()
    assert "Range" in display
    assert "|" in display
    assert "-" in display
    assert "50.00" in display


def test_table_update_and_display():
    table = Table(headers=["Col1", "Col2"], variables=["Var1", "Var2"])
    table.update("Var1", "Col1", 100)
    table.update("Var2", "Col2", 200)
    display = table.display()
    assert "Col1" in display
    assert "Col2" in display
    assert "100" in display
    assert "200" in display


def test_log_monitor_update_and_display():
    log_monitor = LogMonitor(max_logs=3, timestamp=False)
    log_monitor.update("First log")
    log_monitor.update("Second log")
    log_monitor.update("Third log")
    log_monitor.update("Fourth log")  # Exceeds max_logs
    display = log_monitor.display()
    assert "First log" not in display  # Should be removed
    assert "Second log" in display
    assert "Third log" in display
    assert "Fourth log" in display


def test_indicator_lamp_update_and_display():
    lamp = IndicatorLamp(label="Test Lamp", on_color="green", off_color="red")
    lamp.update(True)
    assert "Test Lamp: \033[1;greenm●\033[0m" in lamp.display()
    lamp.update(False)
    assert "Test Lamp: \033[1;redm●\033[0m" in lamp.display()


def test_machine_state_update_and_display():
    states = ["State1", "State2", "State3"]
    machine_state = MachineState(states=states)
    machine_state.update(5)  # Binary: 101
    assert machine_state.as_dict() == {"State1": True, "State2": False, "State3": True}
    assert int(machine_state.display()) == 101


def test_monitor_group_add_and_update_elements():
    text_element = TextElement(text="Hello")
    progress_element = ProgressBar(total_steps=10, label="Progress")
    group = MonitorGroup(group_id="group1", elements={"text": text_element})
    group.add_element("progress", progress_element)
    assert "group1.text" in group.elements
    assert "group1.progress" in group.elements

    group.update_element("group1.text", "New Text")
    assert group.elements["group1.text"].display() == "New Text"

    group.update_element("group1.progress", 5)
    assert "50.0%" in group.elements["group1.progress"].display()


if __name__ == "__main__":
    pytest.main()
