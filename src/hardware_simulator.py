from config import CLASS_NAMES
from hardware_interface import HardwareInterface


class HardwareSimulator(HardwareInterface):
    """Laptop-only stand-in for the future Raspberry Pi + STM32 hardware path."""

    def __init__(self):
        self.connected = False
        self.state = "DISCONNECTED"

    def connect(self):
        self.connected = True
        self.state = "READY"
        return True

    def disconnect(self):
        self.connected = False
        self.state = "DISCONNECTED"
        return True

    def ping(self) -> bool:
        return self.connected

    def send_sort_command(self, class_name: str, confidence: float) -> bool:
        if class_name not in CLASS_NAMES:
            raise ValueError(
                f"Invalid class '{class_name}'. Expected one of: {', '.join(CLASS_NAMES)}"
            )
        if not 0.0 <= confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        if not self.connected:
            self.connect()

        self.state = "SORTING"
        print(f"Sending command to STM32: SORT class={class_name} confidence={confidence:.2f}")
        print("STM32: ACK")
        print(f"STM32: rotating chute to {class_name} bin")
        print("STM32: opening trapdoor")
        print("STM32: sorting complete")
        print("STM32: DONE")
        self.state = "READY"
        return True

    def get_status(self) -> dict:
        return {
            "connected": self.connected,
            "state": self.state,
            "mode": "sim",
        }


def send_sort_command(class_name: str, confidence: float) -> bool:
    """Backward-compatible wrapper used by the existing laptop demo scripts."""
    simulator = HardwareSimulator()
    return simulator.send_sort_command(class_name, confidence)
