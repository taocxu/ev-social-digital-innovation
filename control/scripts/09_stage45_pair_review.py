from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from common import CONTROL_DIR, now_iso, read_csv, write_csv


def main() -> int:
    class_dir = CONTROL_DIR / "classification"
    pairs = read_csv(class_dir / "DOCX_PDF_PAIR_MAP.csv")
    classifications = read_csv(class_dir / "CLASSIFICATION_MAP.csv")
    by_id = {r["file_id"]: r for r in classifications}
    for row in pairs:
        docx_role = by_id[row["docx_file_id"]]["document_role"]
        pdf_role = by_id[row["pdf_file_id"]]["document_role"]
        row["docx_document_role"] = docx_role
        row["pdf_document_role"] = pdf_role
        if row["matching_basis"] == "exact basename":
            row["stage45_pair_status"] = "confirmed_same_basename_export_pair"
            row["stage45_reason"] = "Exact basename plus compatible content identity; retained as a DOCX/PDF export or release pair."
            row["requires_human_review"] = "false"
        elif row["pair_id"] == "pair_0007":
            row["stage45_pair_status"] = "candidate_bilingual_title_release_pair"
            row["stage45_reason"] = "Different filenames but extracted document titles align; likely Chinese submission DOCX and English-titled PDF release."
            row["requires_human_review"] = "true"
        elif row["pair_id"] == "pair_0008":
            row["stage45_pair_status"] = "candidate_date_aligned_export_pair"
            row["stage45_reason"] = "21Nov identifiers and high title similarity support a likely version export, but basename is not exact."
            row["requires_human_review"] = "true"
        elif row["pair_id"] == "pair_0009":
            row["stage45_pair_status"] = "candidate_same_family_pdf_pair"
            row["stage45_reason"] = "Same manuscript family, but V1.5 DOCX and TX1906 PDF labels do not prove a direct export event."
            row["requires_human_review"] = "true"
        else:
            row["stage45_pair_status"] = "supporting_attachment_relationship_not_export"
            row["stage45_reason"] = "The PDF is labelled submission-support material rather than a direct export of the short report; relationship retained but not treated as a release pair."
            row["pair_type"] = "DOCX_PDF_supporting_attachment_relationship"
            row["requires_human_review"] = "true"
    fields = list(pairs[0].keys())
    write_csv(class_dir / "DOCX_PDF_PAIR_MAP.csv", pairs, fields)

    versions = read_csv(class_dir / "VERSION_RELATIONSHIP_MAP.csv")
    family_one = [r for r in versions if r["relationship_id"] == "ver_0001"]
    pair_nine = next((r for r in pairs if r["pair_id"] == "pair_0009"), None)
    if family_one and pair_nine and pair_nine["pdf_file_id"] not in {r["file_id"] for r in versions}:
        fid = pair_nine["pdf_file_id"]
        cls = by_id[fid]
        cls["document_family"] = family_one[0]["document_family"]
        versions.append({
            "relationship_id": "ver_0001", "document_family": family_one[0]["document_family"],
            "file_id": fid, "source_path": cls["source_path"], "filename": cls["original_filename"],
            "extension": ".pdf", "version_marker": "pdf_release", "track_changes_status": "",
            "relationship_type": "candidate_same_family_pdf_release", "related_file_ids": "",
            "candidate_authoritative_version": "false",
            "candidate_reason": "PDF title and pair-map evidence place it in the family, but the direct source DOCX version remains uncertain.",
            "confidence": "medium", "requires_human_review": "true",
            "earliest_identified_version": family_one[0]["earliest_identified_version"],
            "latest_clean_candidate": family_one[0]["latest_clean_candidate"],
            "latest_tracked_candidate": family_one[0]["latest_tracked_candidate"],
            "submission_candidate": family_one[0]["submission_candidate"], "pdf_release": "true",
            "component_or_full_document": "full_document", "parent_file_id": "",
            "authoritative_status": "historical_version", "text_similarity_to_family_max": "",
        })
        family_ids = [r["file_id"] for r in versions if r["relationship_id"] == "ver_0001"]
        for r in versions:
            if r["relationship_id"] == "ver_0001":
                r["related_file_ids"] = ";".join(x for x in family_ids if x != r["file_id"])
        write_csv(class_dir / "CLASSIFICATION_MAP.csv", classifications, list(classifications[0].keys()))
    groups = defaultdict(list)
    for row in versions:
        groups[row["relationship_id"]].append(row)
    write_csv(class_dir / "VERSION_RELATIONSHIP_MAP.csv", versions, list(versions[0].keys()))
    lines = ["# Version history report after Stage 4.5", "", f"Generated: {now_iso()}", "", "Candidate fields are evidence-based prompts only; no unique authoritative version is assigned.", ""]
    for relationship_id, group in sorted(groups.items()):
        first = group[0]
        lines += [f"## {first['document_family']}", "", f"- Earliest identified file_id: `{first['earliest_identified_version']}`", f"- Latest clean candidate: `{first['latest_clean_candidate']}`", f"- Latest tracked candidate: `{first['latest_tracked_candidate']}`", f"- Submission candidate: `{first['submission_candidate']}`", ""]
        for row in group:
            lines.append(f"- `{row['filename']}` — {row['component_or_full_document']}; {row['authoritative_status']}; PDF release={row['pdf_release']}")
        lines.append("")
    (CONTROL_DIR / "reports" / "VERSION_HISTORY_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    result = {
        "generated": now_iso(), "pairs": len(pairs),
        "confirmed_exact": sum(r["stage45_pair_status"] == "confirmed_same_basename_export_pair" for r in pairs),
        "candidate_or_supporting": sum(r["stage45_pair_status"] != "confirmed_same_basename_export_pair" for r in pairs),
    }
    (CONTROL_DIR / "logs" / "09_stage45_pair_review.log").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
