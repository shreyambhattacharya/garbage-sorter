import argparse
import time

from config import (
    CLASS_NAMES,
    SERIAL_BAUDRATE,
    SERIAL_PORT,
    SERIAL_TIMEOUT_SECONDS,
    SORT_COMMAND_TIMEOUT_SECONDS,
)
from hardware_interface import HardwareInterface
from serial_protocol import (
    make_ping_command,
    make_sort_command,
    make_status_command,
    make_test_command,
    parse_response,
)


class SerialHardwareInterface(HardwareInterface):
    """STM32 serial backend using the plain-text sorter command protocol."""

    def __init__(
        self,
        port: str = SERIAL_PORT,
        baudrate: int = SERIAL_BAUDRATE,
        timeout_seconds: float = SERIAL_TIMEOUT_SECONDS,
        sort_timeout_seconds: float = SORT_COMMAND_TIMEOUT_SECONDS,
    ):
        self.port = port
        self.baudrate = baudrate
        self.timeout_seconds = timeout_seconds
        self.sort_timeout_seconds = sort_timeout_seconds
        self.serial_connection = None
        self._serial_module = None
        self._next_command_id = 1

    def connect(self):
        if self.serial_connection is not None and self.serial_connection.is_open:
            return True

        try:
            import serial
        except ModuleNotFoundError:
            print("Serial error: pyserial is not installed. Run: pip install -r requirements.txt")
            return False

        self._serial_module = serial

        try:
            self.serial_connection = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=self.timeout_seconds,
            )
            return True
        except serial.SerialException as exc:
            message = str(exc).lower()
            if "permission" in message or "access is denied" in message:
                print(f"Serial error: permission denied opening {self.port}.")
            else:
                print(f"Serial error: could not open serial port {self.port}: {exc}")
            self.serial_connection = None
            return False

    def disconnect(self):
        if self.serial_connection is not None:
            try:
                self.serial_connection.close()
            finally:
                self.serial_connection = None
        return True

    def ping(self) -> bool:
        if not self._ensure_connected():
            return False

        if not self._write_command(make_ping_command()):
            return False

        response = self._read_response_until(
            lambda parsed: parsed["type"] == "PONG",
            timeout_seconds=self.timeout_seconds,
            waiting_for="PONG",
        )
        return response is not None

    def send_sort_command(self, class_name: str, confidence: float) -> bool:
        if not self._ensure_connected():
            return False

        command_id = self._next_id()
        try:
            command = make_sort_command(class_name, confidence, command_id)
        except ValueError as exc:
            print(f"Sort command error: {exc}")
            return False

        if not self._write_command(command):
            return False

        ack_response = self._read_response_until(
            lambda parsed: self._is_expected_id_response(parsed, "ACK", command_id),
            timeout_seconds=self.timeout_seconds,
            waiting_for=f"ACK id={command_id}",
            command_id=command_id,
        )
        if ack_response is None:
            return False

        done_response = self._read_response_until(
            lambda parsed: self._is_expected_id_response(parsed, "DONE", command_id),
            timeout_seconds=self.sort_timeout_seconds,
            waiting_for=f"DONE id={command_id}",
            command_id=command_id,
        )
        return done_response is not None

    def get_status(self) -> dict:
        if not self._ensure_connected():
            return {"connected": False, "state": "DISCONNECTED", "error": "not connected"}

        if not self._write_command(make_status_command()):
            return {"connected": True, "state": "UNKNOWN", "error": "write failed"}

        response = self._read_response_until(
            lambda parsed: parsed["type"] == "STATUS",
            timeout_seconds=self.timeout_seconds,
            waiting_for="STATUS state=<state>",
        )
        if response is None:
            return {"connected": True, "state": "UNKNOWN", "error": "status timeout"}

        return {"connected": True, "state": response["state"]}

    def run_test_command(self, test_name: str, timeout_seconds: float | None = None) -> bool:
        if not self._ensure_connected():
            return False

        try:
            command = make_test_command(test_name)
        except ValueError as exc:
            print(f"Test command error: {exc}")
            return False

        if not self._write_command(command):
            return False

        return self._read_test_response(
            test_name,
            timeout_seconds=timeout_seconds or self.sort_timeout_seconds,
        )

    def _ensure_connected(self) -> bool:
        if self.serial_connection is not None and self.serial_connection.is_open:
            return True
        return self.connect()

    def _next_id(self) -> int:
        command_id = self._next_command_id
        self._next_command_id += 1
        return command_id

    def _write_command(self, command: str) -> bool:
        try:
            self.serial_connection.write(command.encode("utf-8"))
            self.serial_connection.flush()
            return True
        except Exception as exc:
            print(f"Serial error: failed to write command: {exc}")
            return False

    def _read_line(self) -> str | None:
        try:
            line_bytes = self.serial_connection.readline()
        except Exception as exc:
            print(f"Serial error: failed while reading from STM32: {exc}")
            return None

        if not line_bytes:
            return ""

        try:
            return line_bytes.decode("utf-8", errors="replace").strip()
        except Exception as exc:
            print(f"Serial error: could not decode STM32 response: {exc}")
            return None

    def _read_response_until(
        self,
        predicate,
        timeout_seconds: float,
        waiting_for: str,
        command_id: int | None = None,
    ) -> dict | None:
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            line = self._read_line()
            if line is None:
                return None
            if line == "":
                continue

            parsed = parse_response(line)
            response_type = parsed.get("type")

            if response_type == "MALFORMED":
                print(f"Serial warning: malformed STM32 response: {parsed['raw']}")
                continue

            if response_type == "ERROR":
                if command_id is None or parsed.get("id") == command_id:
                    print(
                        "STM32 returned ERROR"
                        f" id={parsed.get('id')} message={parsed.get('message', '')}"
                    )
                    return None

            if predicate(parsed):
                return parsed

            print(f"Serial warning: unexpected STM32 response while waiting for {waiting_for}: {line}")

        print(f"Serial timeout: timed out waiting for {waiting_for}.")
        return None

    def _read_test_response(self, test_name: str, timeout_seconds: float) -> bool:
        deadline = time.monotonic() + timeout_seconds

        while time.monotonic() < deadline:
            line = self._read_line()
            if line is None:
                return False
            if line == "":
                continue

            parsed = parse_response(line)
            response_type = parsed.get("type")

            if response_type == "MALFORMED":
                print(f"Serial warning: malformed STM32 response: {parsed['raw']}")
                continue

            print(f"STM32: {line}")

            if response_type == "ERROR":
                print(
                    "STM32 returned ERROR"
                    f" id={parsed.get('id')} message={parsed.get('message', '')}"
                )
                return False

            if response_type == "DONE" and parsed.get("test") == test_name:
                return True

        print(f"Serial timeout: timed out waiting for DONE test={test_name}.")
        return False

    @staticmethod
    def _is_expected_id_response(parsed: dict, response_type: str, command_id: int) -> bool:
        return parsed.get("type") == response_type and parsed.get("id") == command_id


def parse_args():
    parser = argparse.ArgumentParser(description="Smoke test the STM32 serial hardware interface.")
    parser.add_argument("--port", default=SERIAL_PORT, help=f"Serial port to open, default {SERIAL_PORT}.")
    parser.add_argument("--baudrate", type=int, default=SERIAL_BAUDRATE)
    parser.add_argument("--timeout", type=float, default=SERIAL_TIMEOUT_SECONDS)
    parser.add_argument("--sort-timeout", type=float, default=SORT_COMMAND_TIMEOUT_SECONDS)
    parser.add_argument("--ping", action="store_true", help="Send PING and expect PONG.")
    parser.add_argument("--sort", choices=CLASS_NAMES, help="Send a SORT command for the chosen class.")
    parser.add_argument("--confidence", type=float, default=0.90, help="Confidence value for --sort.")
    parser.add_argument("--test-diverters", action="store_true", help="Run STM32 TEST_DIVERTERS.")
    parser.add_argument("--test-trapdoor", action="store_true", help="Run STM32 TEST_TRAPDOOR.")
    parser.add_argument("--test-ultrasonic", action="store_true", help="Run STM32 TEST_ULTRASONIC.")
    parser.add_argument("--test-display", action="store_true", help="Run STM32 TEST_DISPLAY.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    requested_tests = [
        ("TEST_DIVERTERS", args.test_diverters),
        ("TEST_TRAPDOOR", args.test_trapdoor),
        ("TEST_ULTRASONIC", args.test_ultrasonic),
        ("TEST_DISPLAY", args.test_display),
    ]

    if not args.ping and args.sort is None and not any(enabled for _, enabled in requested_tests):
        print("No serial action requested. Use --ping, --sort <class>, or a --test-* option.")
        return 0

    hardware = SerialHardwareInterface(
        port=args.port,
        baudrate=args.baudrate,
        timeout_seconds=args.timeout,
        sort_timeout_seconds=args.sort_timeout,
    )

    try:
        if args.ping and not hardware.ping():
            return 1

        if args.sort is not None and not hardware.send_sort_command(args.sort, args.confidence):
            return 1

        for test_name, enabled in requested_tests:
            if enabled and not hardware.run_test_command(test_name):
                return 1

        return 0
    finally:
        hardware.disconnect()


if __name__ == "__main__":
    raise SystemExit(main())
