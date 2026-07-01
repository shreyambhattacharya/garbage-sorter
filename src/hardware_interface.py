class HardwareInterface:
    """Base interface for sorter hardware backends."""

    def connect(self):
        raise NotImplementedError

    def disconnect(self):
        raise NotImplementedError

    def ping(self) -> bool:
        raise NotImplementedError

    def send_sort_command(self, class_name: str, confidence: float) -> bool:
        raise NotImplementedError

    def get_status(self) -> dict:
        raise NotImplementedError
