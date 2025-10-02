import enum
from pydantic import BaseModel


class TestStatus(str, enum.Enum):
    SUCCESS = "success"
    FAIL = "fail"
    ERROR = "error"
    IN_PROGRESS = "in_progress"


class TestRequest(BaseModel):
    test_id: str
    mac_address: str
    serial_number: str
    device_name: str
