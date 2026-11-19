import json

from backend.errors import ProcessingError
from backend.model_bundle import ModelManifest


def read_evaluations(raw: bytes, manifest: ModelManifest) -> dict:
    try:
        payload = json.loads(raw, parse_constant=reject_constant)
        json.dumps(payload, allow_nan=False)
        if not isinstance(payload, dict):
            raise ValueError("Payload evaluasi harus berupa objek.")
        if payload["model_version"] != manifest.model_version:
            raise ValueError("Versi model pada evaluasi berbeda dari metadata.")
        if manifest.source_dataset_version and payload["dataset_version"] != manifest.source_dataset_version:
            raise ValueError("Versi sumber dataset pada evaluasi berbeda dari metadata.")
        for task in ("classification", "regression"):
            section = payload[task]
            if not isinstance(section["cv_candidates"], list) or not section["cv_candidates"]:
                raise ValueError(f"Tabel perbandingan {task} belum tersedia.")
            test = section["test_evaluation"]
            if not test["evaluation_source"]:
                raise ValueError(f"Sumber evaluasi {task} belum tersedia.")
            if (test["model_version"], test["dataset_version"]) != (payload["model_version"], payload["dataset_version"]):
                raise ValueError(f"Versi data uji {task} tidak konsisten.")
        if not payload["clustering"]["candidates"] or not payload["clustering"]["segment_profiles"]:
            raise ValueError("Tabel atau profil clustering belum tersedia.")
    except (ValueError, KeyError, TypeError) as error:
        raise ProcessingError("INVALID_EVALUATIONS", f"Hasil evaluasi tidak valid. {error}") from error
    return payload


def reject_constant(value: str):
    raise ValueError(f"Nilai {value} tidak valid pada JSON evaluasi.")
