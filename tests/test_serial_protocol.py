import sys
from pathlib import Path

SRC_DIR = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC_DIR))

from serial_protocol import parse_response


def test_parse_pong():
    assert parse_response("PONG") == {"type": "PONG"}


def test_parse_ack_with_id():
    assert parse_response("ACK id=1") == {"type": "ACK", "id": 1}


def test_parse_done_with_id():
    assert parse_response("DONE id=1") == {"type": "DONE", "id": 1}


def test_parse_error_with_message():
    assert parse_response("ERROR id=1 message=invalid_class") == {
        "type": "ERROR",
        "id": 1,
        "message": "invalid_class",
    }


def test_parse_status_state():
    assert parse_response("STATUS state=IDLE") == {"type": "STATUS", "state": "IDLE"}


def test_parse_status_test_result():
    assert parse_response("STATUS test=TEST_TRAPDOOR result=START") == {
        "type": "STATUS",
        "test": "TEST_TRAPDOOR",
        "result": "START",
    }


def test_parse_done_test():
    assert parse_response("DONE test=TEST_TRAPDOOR") == {
        "type": "DONE",
        "test": "TEST_TRAPDOOR",
    }


def test_parse_distance():
    assert parse_response("DISTANCE class=recycling valid=1 cm_x100=1234") == {
        "type": "DISTANCE",
        "class": "recycling",
        "valid": True,
        "cm_x100": 1234,
        "distance_cm": 12.34,
    }


def test_parse_malformed_line():
    assert parse_response("DONE test=NOT_A_TEST") == {
        "type": "MALFORMED",
        "raw": "DONE test=NOT_A_TEST",
    }
