import pytest

from backend.dataset import dataset_version, read_dataset
from backend.errors import ProcessingError, read_input

HEADER = "customerID,tenure,Contract,MonthlyCharges,TotalCharges,Churn\n"
ROW = "00123,12,Month-to-month,49.90,598.80,Yes\n"


def parse(text, *, allow_missing=False, categories=None):
    return read_dataset(
        text.encode(), ["TotalCharges"],
        allow_missing_total_charges=allow_missing,
        categories=categories or {},
    )


def test_preserves_id_types_and_preprocessing_inputs():
    rows = parse("\ufeff" + HEADER + ROW + '00456,0,One year,19.85," ",\n', allow_missing=True)
    assert rows == [
        {
            "customerID": "00123", "tenure": 12, "Contract": "Month-to-month",
            "MonthlyCharges": 49.90, "TotalCharges": 598.80, "Churn": "Yes",
        },
        {
            "customerID": "00456", "tenure": 0, "Contract": "One year",
            "MonthlyCharges": 19.85, "TotalCharges": None, "Churn": None,
        },
    ]
    assert isinstance(rows[0]["tenure"], int)
    assert isinstance(rows[0]["MonthlyCharges"], float)
    assert dataset_version(ROW.encode()) != dataset_version(ROW.replace("12", "13").encode())


@pytest.mark.parametrize(("text", "code", "row", "field"), [
    ("", "EMPTY_DATASET", None, None),
    (HEADER, "EMPTY_DATASET", None, None),
    (HEADER.replace("TotalCharges", "Contract") + ROW, "INVALID_HEADER", 1, None),
    (HEADER.replace("TotalCharges", "unused") + ROW, "MISSING_COLUMNS", 1, None),
    (HEADER + ROW + ROW, "DUPLICATE_CUSTOMER_ID", 3, "customerID"),
    (HEADER + ROW + '00456,0,"One year\n', "INVALID_CSV", 3, None),
    (HEADER + "00123,12\n", "INVALID_CSV", 2, None),
    (HEADER + ROW.replace(",12,", ",abc,"), "INVALID_FIELD", 2, "tenure"),
    (HEADER + ROW.replace("49.90", "NaN"), "INVALID_FIELD", 2, "MonthlyCharges"),
    (HEADER + ROW.replace("598.80", " "), "INVALID_FIELD", 2, "TotalCharges"),
])
def test_invalid_csv_reports_operational_context(text, code, row, field):
    with pytest.raises(ProcessingError) as error:
        parse(text)
    assert (error.value.code, error.value.row, error.value.field) == (code, row, field)


def test_categories_follow_data_policy():
    parse(HEADER + ROW, categories={"Contract": ["Month-to-month"]})
    with pytest.raises(ProcessingError) as error:
        parse(HEADER + ROW, categories={"Contract": ["One year"]})
    assert error.value.field == "Contract"


def test_missing_csv_has_actionable_error(tmp_path):
    with pytest.raises(ProcessingError) as error:
        read_input(tmp_path / "telco.csv", "DATASET", "Dataset")
    assert error.value.code == "DATASET_NOT_FOUND"
    assert "telco.csv" in str(error.value)
