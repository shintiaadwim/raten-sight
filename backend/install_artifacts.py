"""Install a received data/outputs directory or an exported artifact directory."""

import argparse
import json
from hashlib import sha256
from pathlib import Path
from tempfile import NamedTemporaryFile

from backend.errors import ProcessingError, read_input
from backend.evaluations import read_evaluations
from backend.model_bundle import artifact_paths, check_dependencies, load_pipelines, read_manifest


def install(source: Path, destination: Path) -> Path:
    metadata_path = source / "model_metadata.json"
    if not metadata_path.is_file():
        metadata_path = source / "artifacts" / "model_metadata.json"
    raw, manifest = read_manifest(metadata_path)
    check_dependencies(manifest)
    files = {
        kind: read_input(path, "ARTIFACT", "Artefak model")
        for kind, path in artifact_paths(metadata_path, manifest).items()
    }
    load_pipelines(manifest, files)
    evaluation = None
    if manifest.evaluations:
        evaluation_path = metadata_path.with_name(manifest.evaluations)
        if not evaluation_path.is_file():
            evaluation_path = source / manifest.evaluations
        evaluation = read_input(evaluation_path, "EVALUATIONS", "Hasil evaluasi")
        read_evaluations(evaluation, manifest)
    if metadata_path.parent.resolve() == destination.resolve():
        return metadata_path
    document = json.loads(raw)
    native_metadata = "models" in document
    for kind, spec in manifest.pipelines.items():
        original = Path(spec.artifact)
        name = f"{original.stem}.{sha256(files[kind]).hexdigest()}{original.suffix}"
        write_file(destination / name, files[kind])
        if native_metadata:
            document["artifacts"][kind] = name
        else:
            document[kind]["artifact"] = name
    if evaluation is not None:
        name = f"evaluations.{sha256(evaluation).hexdigest()}.json"
        write_file(destination / name, evaluation)
        document["evaluations_file" if native_metadata else "evaluations"] = name
    installed_metadata = destination / "model_metadata.json"
    write_file(installed_metadata, json.dumps(document, ensure_ascii=False, allow_nan=False).encode("utf-8"))
    return installed_metadata


def write_file(path: Path, content: bytes) -> None:
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with NamedTemporaryFile("wb", dir=path.parent, suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(content)
        temporary.replace(path)
    except OSError as error:
        raise ProcessingError("INSTALL_FAILED", f"Gagal memasang {path.name}.") from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pasang paket model Data yang diterima lewat folder terpisah.")
    parser.add_argument("source", type=Path, help="Folder data/outputs atau folder berisi model_metadata.json.")
    parser.add_argument("--destination", type=Path, default=Path(__file__).resolve().parent / "artifacts")
    args = parser.parse_args()
    try:
        path = install(args.source, args.destination)
    except ProcessingError as error:
        parser.exit(1, f"{error.code}: {error}\n")
    print(f"Paket model terpasang: {path}")


if __name__ == "__main__":
    main()
