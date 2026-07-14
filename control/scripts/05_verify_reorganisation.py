from __future__ import annotations

import argparse
import json
from pathlib import Path

from common import CONTROL_DIR, load_config, now_iso, read_csv, sha256_file, workspace_path


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify an explicitly created copy-based reorganisation")
    parser.add_argument("--allow-missing-target", action="store_true", help="Report an absent target without failing")
    args = parser.parse_args()
    config = load_config()
    target_root = Path(config["reorg_root"])
    inventory = {r["file_id"]: r for r in read_csv(workspace_path(config["inventory_csv"]))}
    classification = read_csv(workspace_path(config["classification_csv"]))
    if not target_root.exists():
        result = {"generated": now_iso(), "status": "target_not_created", "target": str(target_root), "verified": 0, "errors": []}
        (CONTROL_DIR / "logs" / "05_verify_reorganisation.log").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(result, ensure_ascii=False))
        return 0 if args.allow_missing_target else 2
    errors, verified = [], 0
    for row in classification:
        if row["copy_action"] != "copy":
            continue
        inv = inventory[row["file_id"]]
        target = target_root / Path(row["proposed_target_relative_path"])
        if not target.is_file():
            errors.append(f"Missing: {target}")
            continue
        if target.stat().st_size != int(inv["size_bytes"]):
            errors.append(f"Size mismatch: {target}")
            continue
        if sha256_file(target) != inv["sha256"]:
            errors.append(f"SHA-256 mismatch: {target}")
            continue
        verified += 1
    result = {"generated": now_iso(), "status": "pass" if not errors else "fail", "target": str(target_root), "verified": verified, "errors": errors}
    (CONTROL_DIR / "logs" / "05_verify_reorganisation.log").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
