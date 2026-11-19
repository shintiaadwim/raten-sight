"""Translate the Data team's exported metadata into the runtime model contract."""

import ast
import re
from itertools import product


def runtime_manifest(metadata: dict) -> dict:
    models = metadata["models"]
    classifier = models["classification"]
    clusterer = models["clustering"]
    regressor = models["regression"]
    retention = metadata["retention_simulation_rules"]
    noise = clusterer["noise_handling_policy"]
    segments = [
        {"segment_id": int(segment_id), "segment_name": name}
        for segment_id, name in clusterer["segment_id_to_name"].items()
    ]
    noise_label = None
    if noise["selected_model_produces_noise"]:
        noise_label = noise["noise_label"]
        if noise_label not in {segment["segment_id"] for segment in segments}:
            segments.append({"segment_id": noise_label, "segment_name": noise["fallback_segment_name"]})

    # run_pipeline.py encodes Churn == "Yes" as 1 before fitting the classifier.
    if classifier["positive_class"] != "Yes" or metadata["id_column"] != "customerID":
        raise ValueError("Paket Data harus memakai customerID dan kelas churn Yes.")
    rules = []
    for rule in sorted(retention["rules"], key=lambda item: item["priority"]):
        for condition in rule_conditions(rule["condition"]):
            rules.append({**condition, "recommendation": rule["recommendation"]})
    return {
        "model_version": metadata["model_version"],
        "dependencies": metadata["dependencies"],
        "allow_missing_total_charges": True,
        "classification": {
            "artifact": metadata["artifacts"]["classification"],
            "algorithm": classifier["selected_model"],
            "features": classifier["required_features"],
            "positive_class": 1,
            "threshold": classifier["threshold"],
        },
        "clustering": {
            "artifact": metadata["artifacts"]["clustering"],
            "algorithm": clusterer["selected_model"],
            "features": clusterer["required_features"],
            "segments": segments,
            "noise_label": noise_label,
        },
        "regression": {
            "artifact": metadata["artifacts"]["regression"],
            "algorithm": regressor["selected_model"],
            "features": regressor["required_features"],
            "target": regressor["target_column"],
            "unit": regressor["currency_unit"],
        },
        "retention_rules": rules,
        "fallback_recommendation": retention["missing_input_fallback"],
        "source_dataset_version": metadata["dataset_version"],
        "source_dataset_sha256": metadata.get("dataset_sha256"),
        "evaluations": metadata.get("evaluations_file", "evaluations_payload.json"),
    }


def rule_conditions(text: str) -> list[dict]:
    if text.startswith("Default (") and text.endswith(")"):
        return [{}]
    expression = re.sub(r"\s*\(prob >= [0-9.]+\)", "", text)
    for original, replacement in (("AND", "and"), ("OR", "or"), ("IN", "in")):
        expression = re.sub(rf"\b{original}\b", replacement, expression)
    return condition_clauses(ast.parse(expression, mode="eval").body)


def condition_clauses(node: ast.AST) -> list[dict]:
    if isinstance(node, ast.BoolOp):
        children = [condition_clauses(value) for value in node.values]
        if isinstance(node.op, ast.Or):
            return [clause for child in children for clause in child]
        if isinstance(node.op, ast.And):
            combined = []
            for clauses in product(*children):
                merged = {}
                for clause in clauses:
                    if merged.keys() & clause.keys():
                        raise ValueError("Kondisi retensi mengulang field yang sama dalam satu AND.")
                    merged.update(clause)
                combined.append(merged)
            return combined
    if isinstance(node, ast.Compare) and isinstance(node.left, ast.Name) and len(node.ops) == 1:
        field = node.left.id
        value = ast.literal_eval(node.comparators[0])
        op = node.ops[0]
        if field == "churn_probability":
            if isinstance(op, ast.GtE):
                return [{"min_probability": value}]
            if isinstance(op, ast.LtE):
                return [{"max_probability": value}]
        if field == "churn_prediction" and isinstance(op, ast.Eq):
            return [{"churn_prediction": value}]
        if field == "segment_id":
            if isinstance(op, ast.Eq):
                return [{"segment_ids": [value]}]
            if isinstance(op, ast.In) and isinstance(value, (list, tuple)):
                return [{"segment_ids": list(value)}]
    raise ValueError("Kondisi retensi tidak didukung oleh kontrak Backend.")
