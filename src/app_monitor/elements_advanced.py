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


# Machine state class
class MachineState(MonitorElement):
    """Class for rendering machine states using binary values."""

    def __init__(self, element_id=None, states=None):
        """
        Initialize a MachineState.

        Args:
            states (list): List of state names.
        """
        super().__init__(element_id)
        self.states = states or []
        self.state_binary = "0" * len(self.states)

    def update(self, state):
        """Update the state with a new binary value."""
        self.state_binary = format(int(state), "032b")

    def display(self):
        """Render the machine state binary string."""
        return self.state_binary

    def as_dict(self):
        """Convert the binary state to a dictionary of named states."""
        return {
            state: bool(int(bit))
            for state, bit in zip(self.states, self.state_binary[::-1])
        }
