class SorterStateMachine:
    STATES = {
        "IDLE",
        "CAPTURING",
        "CLASSIFYING",
        "UNCERTAIN",
        "ACCEPTED",
        "SENDING_COMMAND",
        "SORTING",
        "COMPLETE",
        "ERROR",
    }

    def __init__(self):
        self.current_state = "IDLE"
        self.last_prediction = None
        self.last_confidence = None
        self.last_error = None
        self.last_command_id = None

    def set_state(self, state: str) -> None:
        if state not in self.STATES:
            raise ValueError(f"Invalid sorter state '{state}'.")
        self.current_state = state

    def set_error(self, error_message: str) -> None:
        self.last_error = error_message
        self.current_state = "ERROR"

    def reset(self) -> None:
        self.current_state = "IDLE"
        self.last_prediction = None
        self.last_confidence = None
        self.last_error = None
        self.last_command_id = None

    def as_dict(self) -> dict:
        return {
            "current_state": self.current_state,
            "last_prediction": self.last_prediction,
            "last_confidence": self.last_confidence,
            "last_error": self.last_error,
            "last_command_id": self.last_command_id,
        }
