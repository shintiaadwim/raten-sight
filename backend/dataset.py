import csv
import re
from collections.abc import Collection, Mapping
from hashlib import sha256
from io import StringIO
from math import isfinite
from typing import TypeAlias

from backend.errors import ProcessingError

CATEGORICAL_FIELDS = frozenset({
    "gender", "Partner", "Dependents", "PhoneService", "MultipleLines", "InternetService",
    "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV",
    "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod",
})
INTEGER_FIELDS = frozenset({"tenure", "SeniorCitizen"})
AMOUNT_FIELDS = frozenset({"MonthlyCharges", "TotalCharges"})
FEATURE_FIELDS = CATEGORICAL_FIELDS | INTEGER_FIELDS | AMOUNT_FIELDS
SUMMARY_FIELDS = frozenset({"customerID", "tenure", "Contract", "MonthlyCharges"})
DECIMAL = re.compile(r"[0-9]+(?:\.[0-9]+)?")

CustomerRow: TypeAlias = dict[str, str | int | float | None]


def dataset_version(content: bytes) -> str:
    return f"sha256:{sha256(content).hexdigest()}"


def read_dataset(
    content: bytes,
    features: Collection[str],
    *,
    allow_missing_total_charges: bool,
    categories: Mapping[str, Collection[str]],
) -> list[CustomerRow]:
    try:
        decoded = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ProcessingError("INVALID_CSV", "CSV harus menggunakan UTF-8.") from error
    if not decoded.strip():
        raise ProcessingError("EMPTY_DATASET", "File CSV kosong.")
    if "\x00" in decoded:
        raise ProcessingError("INVALID_CSV", "CSV mengandung karakter yang tidak valid.")

    reader = csv.reader(StringIO(decoded, newline=""), strict=True)
    required_fields = SUMMARY_FIELDS | set(features)
    customers = []
    seen_ids = set()
    try:
        header = next(reader)
        if not header or any(not field.strip() for field in header) or len(header) != len(set(header)):
            raise ProcessingError("INVALID_HEADER", "Header CSV kosong atau memiliki kolom duplikat.", row=1)
        missing = sorted(required_fields - set(header))
        if missing:
            raise ProcessingError("MISSING_COLUMNS", "Kolom wajib tidak tersedia: " + ", ".join(missing), row=1)
        selected = [(index, field) for index, field in enumerate(header) if field in required_fields or field == "Churn"]
        for values in reader:
            if not values:
                continue
            line = reader.line_num
            if len(values) != len(header):
                raise ProcessingError("INVALID_CSV", "Jumlah nilai tidak sesuai dengan header CSV.", row=line)
            customer = {
                field: parse_value(values[index].strip(), field, line, allow_missing_total_charges, categories)
                for index, field in selected
            }
            customer_id = customer["customerID"]
            if customer_id in seen_ids:
                raise ProcessingError("DUPLICATE_CUSTOMER_ID", "customerID duplikat.", row=line, field="customerID")
            seen_ids.add(customer_id)
            customers.append(customer)
    except csv.Error as error:
        raise ProcessingError("INVALID_CSV", "Format CSV rusak.", row=reader.line_num) from error
    if not customers:
        raise ProcessingError("EMPTY_DATASET", "CSV harus berisi minimal satu pelanggan.")
    return customers


def parse_value(
    value: str,
    field: str,
    row: int,
    allow_missing_total_charges: bool,
    categories: Mapping[str, Collection[str]],
) -> str | int | float | None:
    if not value and (field == "Churn" or (field == "TotalCharges" and allow_missing_total_charges)):
        return None
    if not value:
        raise ProcessingError("INVALID_FIELD", f"Kolom {field} tidak boleh kosong.", row=row, field=field)
    if field in INTEGER_FIELDS:
        if field == "SeniorCitizen" and value not in {"0", "1"}:
            raise ProcessingError("INVALID_FIELD", "Kolom SeniorCitizen harus berisi 0 atau 1.", row=row, field=field)
        try:
            if value.isascii() and value.isdecimal():
                return int(value)
        except ValueError:
            pass
        raise ProcessingError(
            "INVALID_FIELD", f"Kolom {field} harus berisi bilangan bulat nonnegatif.", row=row, field=field,
        )
    if field in AMOUNT_FIELDS:
        if DECIMAL.fullmatch(value) and isfinite(amount := float(value)):
            return amount
        raise ProcessingError(
            "INVALID_FIELD", f"Kolom {field} harus berisi angka desimal nonnegatif.", row=row, field=field,
        )
    allowed = ("Yes", "No") if field == "Churn" else categories.get(field)
    if allowed is not None and value not in allowed:
        raise ProcessingError("INVALID_FIELD", f"Kategori pada kolom {field} tidak dikenali.", row=row, field=field)
    return value
