from config import CLASS_NAMES


def send_sort_command(class_name: str, confidence: float) -> None:
    """Simulate sending a sort command to future STM32-controlled hardware."""
    if class_name not in CLASS_NAMES:
        raise ValueError(
            f"Invalid class '{class_name}'. Expected one of: {', '.join(CLASS_NAMES)}"
        )

    print(f"Sending command to STM32: SORT {class_name} CONF={confidence:.2f}")
    print("STM32: ACK")
    print(f"STM32: rotating chute to {class_name} bin")
    print("STM32: opening trapdoor")
    print("STM32: sorting complete")
