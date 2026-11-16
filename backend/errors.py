from pathlib import Path


class ProcessingError(Exception):
    def __init__(self, code: str, message: str, *, row: int | None = None, field: str | None = None):
        super().__init__(message)
        self.code = code
        self.row = row
        self.field = field

    def as_dict(self) -> dict:
        error = {"code": self.code, "message": str(self)}
        if self.row is not None:
            error["row"] = self.row
        if self.field is not None:
            error["field"] = self.field
        return error


def read_input(path: Path, kind: str, label: str) -> bytes:
    try:
        return path.read_bytes()
    except FileNotFoundError as error:
        raise ProcessingError(f"{kind}_NOT_FOUND", f"{label} '{path.name}' belum tersedia.") from error
    except OSError as error:
        raise ProcessingError(f"{kind}_READ_ERROR", f"{label} '{path.name}' gagal dibaca.") from error
