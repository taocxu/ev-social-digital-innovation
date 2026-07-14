from __future__ import annotations

import argparse
import json
from collections import defaultdict

from common import CONTROL_DIR, load_config, now_iso, read_csv, workspace_path


def main() -> int:
    argparse.ArgumentParser(description="Generate a local master index from approved classification").parse_args()
    config = load_config()
    rows = read_csv(workspace_path(config["classification_csv"]))
    grouped = defaultdict(list)
    for row in rows:
        grouped[row["document_role"]].append(row)
    lines = ["# Master file index", "", f"Generated: {now_iso()}", "", "This index is generated from the proposed classification. It does not assert authority and does not imply that copying has occurred.", ""]
    for role, items in sorted(grouped.items()):
        lines += [f"## {role}", "", "| file_id | Original filename | Theme | Version status | Proposed target | Confidence |", "|---|---|---|---|---|---|"]
        for r in sorted(items, key=lambda x: x["original_filename"].casefold()):
            lines.append(f"| `{r['file_id']}` | {r['original_filename'].replace('|', '&#124;')} | {r['project_theme']} | {r['version_status']} | `{r['proposed_target_relative_path'].replace('|', '&#124;')}` | {r['confidence']} |")
        lines.append("")
    output = CONTROL_DIR / "reports" / "MASTER_FILE_INDEX.md"
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    (CONTROL_DIR / "logs" / "06_generate_master_index.log").write_text(json.dumps({"generated": now_iso(), "records": len(rows), "output": str(output)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(rows), "output": str(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
