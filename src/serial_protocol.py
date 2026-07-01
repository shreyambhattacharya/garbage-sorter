from config import CLASS_NAMES


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
            if values is None or set(values) != {"id"}:
                return malformed(raw)
            command_id = parse_int(values["id"])
            if command_id is None:
                return malformed(raw)
            return {"type": response_type, "id": command_id}

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
            if values is None or set(values) != {"state"}:
                return malformed(raw)
            return {"type": "STATUS", "state": values["state"]}

        return malformed(raw)
    except Exception:
        return malformed(raw)
