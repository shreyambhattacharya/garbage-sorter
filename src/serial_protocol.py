from config import CLASS_NAMES

TEST_COMMANDS = {
    "TEST_DIVERTERS",
    "TEST_TRAPDOOR",
    "TEST_ULTRASONIC",
    "TEST_DISPLAY",
}


def validate_class_name(class_name: str) -> None:
    if class_name not in CLASS_NAMES:
        raise ValueError(
            f"Invalid class '{class_name}'. Expected one of: {', '.join(CLASS_NAMES)}"
        )


def validate_confidence(confidence: float) -> None:
    if not 0.0 <= confidence <= 1.0:
        raise ValueError("confidence must be between 0.0 and 1.0")


def validate_command_id(command_id: int) -> None:
    if not isinstance(command_id, int) or command_id <= 0:
        raise ValueError("command_id must be a positive integer")


def make_ping_command() -> str:
    return "PING\n"


def make_sort_command(class_name: str, confidence: float, command_id: int) -> str:
    validate_class_name(class_name)
    validate_confidence(confidence)
    validate_command_id(command_id)
    return f"SORT class={class_name} confidence={confidence:.4f} id={command_id}\n"


def make_status_command() -> str:
    return "STATUS\n"


def make_reset_command() -> str:
    return "RESET\n"


def make_test_command(test_name: str) -> str:
    if test_name not in TEST_COMMANDS:
        raise ValueError(f"Invalid test command '{test_name}'. Expected one of: {', '.join(sorted(TEST_COMMANDS))}")
    return f"{test_name}\n"


def make_test_diverters_command() -> str:
    return make_test_command("TEST_DIVERTERS")


def make_test_trapdoor_command() -> str:
    return make_test_command("TEST_TRAPDOOR")


def make_test_ultrasonic_command() -> str:
    return make_test_command("TEST_ULTRASONIC")


def make_test_display_command() -> str:
    return make_test_command("TEST_DISPLAY")


def parse_key_value_tokens(tokens: list[str]) -> dict | None:
    values = {}
    for token in tokens:
        if "=" not in token:
            return None
        key, value = token.split("=", 1)
        if not key or value == "":
            return None
        values[key] = value
    return values


def parse_int(value: str) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def malformed(raw: str) -> dict:
    return {"type": "MALFORMED", "raw": raw}


def parse_response(line: str) -> dict:
    raw = line
    try:
        stripped = line.strip()
        if not stripped:
            return malformed(raw)

        response_type, *rest = stripped.split()

        if response_type == "PONG":
            if rest:
                return malformed(raw)
            return {"type": "PONG"}

        if response_type in {"ACK", "DONE"}:
            values = parse_key_value_tokens(rest)
            if values is None:
                return malformed(raw)
            if set(values) == {"id"}:
                command_id = parse_int(values["id"])
                if command_id is None:
                    return malformed(raw)
                return {"type": response_type, "id": command_id}
            if response_type == "DONE" and set(values) == {"test"}:
                if values["test"] not in TEST_COMMANDS:
                    return malformed(raw)
                return {"type": "DONE", "test": values["test"]}
            return malformed(raw)

        if response_type == "ERROR":
            if len(rest) < 2 or not rest[0].startswith("id="):
                return malformed(raw)

            command_id = parse_int(rest[0].split("=", 1)[1])
            message_text = " ".join(rest[1:])
            if command_id is None or not message_text.startswith("message="):
                return malformed(raw)

            return {
                "type": "ERROR",
                "id": command_id,
                "message": message_text.split("=", 1)[1],
            }

        if response_type == "STATUS":
            values = parse_key_value_tokens(rest)
            if values is None:
                return malformed(raw)
            if set(values) == {"state"}:
                return {"type": "STATUS", "state": values["state"]}
            if set(values) == {"test", "result"}:
                if values["test"] not in TEST_COMMANDS:
                    return malformed(raw)
                return {"type": "STATUS", "test": values["test"], "result": values["result"]}
            return malformed(raw)

        if response_type == "DISTANCE":
            values = parse_key_value_tokens(rest)
            if values is None or set(values) != {"class", "valid", "cm_x100"}:
                return malformed(raw)
            if values["class"] not in CLASS_NAMES:
                return malformed(raw)
            valid = parse_int(values["valid"])
            cm_x100 = parse_int(values["cm_x100"])
            if valid not in {0, 1} or cm_x100 is None:
                return malformed(raw)
            return {
                "type": "DISTANCE",
                "class": values["class"],
                "valid": bool(valid),
                "cm_x100": cm_x100,
                "distance_cm": cm_x100 / 100.0,
            }

        return malformed(raw)
    except Exception:
        return malformed(raw)
