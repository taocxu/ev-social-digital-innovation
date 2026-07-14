from __future__ import annotations

import argparse
import csv
import json
import re
from collections import defaultdict
from difflib import SequenceMatcher
from pathlib import Path

from common import CONTROL_DIR, load_config, now_iso, read_csv, workspace_path, write_csv

VERSION_FIELDS = [
    "relationship_id", "document_family", "file_id", "source_path", "filename", "extension",
    "version_marker", "track_changes_status", "relationship_type", "related_file_ids",
    "candidate_authoritative_version", "candidate_reason", "confidence", "requires_human_review",
]
COMPONENT_FIELDS = [
    "relationship_id", "parent_file_id", "component_file_id", "parent_path", "component_path",
    "relationship_type", "relationship_reason", "confidence", "requires_human_review",
]
PAIR_FIELDS = [
    "pair_id", "docx_file_id", "pdf_file_id", "docx_path", "pdf_path", "pair_type",
    "matching_basis", "confidence", "requires_human_review",
]
DUP_FIELDS = [
    "relationship_id", "file_id_a", "file_id_b", "path_a", "path_b", "relationship_type",
    "sha256_equal", "filename_similarity", "content_similarity", "size_ratio", "reason",
    "confidence", "independent_historical_significance", "requires_human_review",
]

VERSION_WORDS = re.compile(
    r"(?:\b(?:draft|final|version|ver|copy|new|clean|submit|submission|backup|revised|reviewed|v)\b|"
    r"最终版|定稿|提交版本|填写|材料整理|备份|留痕|修改|修订|清洁版|废案|新任务tbd)", re.I
)
DATE_VERSION = re.compile(
    r"(?:^|[_\-\s（(])(?:v?\d+(?:\.\d+){0,2}|\d{1,2}(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)|"
    r"\d{1,2}[月.-]\d{1,2}|\d{4}[-_.]?\d{1,2}[-_.]?\d{0,2}|\d{4,8})(?=$|[_\-\s）)])", re.I
)


def norm(value: str) -> str:
    value = Path(value).stem.casefold()
    value = VERSION_WORDS.sub(" ", value)
    value = re.sub(r"(?:_?\d{1,2}(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)(?:\d{2,4})?(?:v\d+(?:\.\d+)*)?)$", " ", value, flags=re.I)
    value = re.sub(r"(?:_?v\d+(?:\.\d+)*)$", " ", value, flags=re.I)
    value = re.sub(r"(?:[_\-]?\d{1,8}(?:\.\d+)?(?:[_\-]\d{1,8})*)$", " ", value)
    value = re.sub(r"(?:[_\-]?(?:材料整理|材料|填写)(?:[_\-]?\d+)?)$", " ", value)
    value = re.sub(r"(?:_?刘丽[（(]?\s*[）)]?)$", " ", value)
    value = DATE_VERSION.sub(" ", value)
    value = re.sub(r"tx\s*\d+", " ", value, flags=re.I)
    value = re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", value)
    return re.sub(r"\s+", " ", value).strip()


def family_key(row: dict) -> str:
    title = norm(row.get("document_title", ""))
    stem = norm(row["filename"])
    if title and 6 <= len(title) <= 160 and not title.startswith(("http", "www")):
        if SequenceMatcher(None, title, stem).ratio() >= 0.38:
            return title
    return stem


def similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a, b).ratio()


def text_signature(row: dict) -> str:
    text = (row.get("document_title", "") + " " + row.get("headings_or_slide_titles", "") + " " + row.get("text_excerpt", "")[:8000]).casefold()
    return re.sub(r"\s+", " ", re.sub(r"[^0-9a-z\u3400-\u9fff]+", " ", text)).strip()


def version_marker(filename: str, track: str) -> str:
    marks = []
    patterns = [
        (r"提交|submission|submit", "submission"), (r"留痕|track", "track_changes"),
        (r"备份|backup|copy", "backup"), (r"废案|abandon", "abandoned"),
        (r"draft|草稿", "draft"), (r"final|最终|定稿", "final_label"),
        (r"v\s*\d+(?:\.\d+)*", "version_number"),
    ]
    for pattern, label in patterns:
        if re.search(pattern, filename, re.I):
            marks.append(label)
    if track == "true" and "track_changes" not in marks:
        marks.append("track_changes_detected")
    return ";".join(marks) or "unmarked"


def is_project_manuscript(row: dict) -> bool:
    rel = Path(row["original_relative_path"])
    if len(rel.parts) == 1 and row["extension"] in {".docx", ".pptx"}:
        return row["probable_document_role"] not in {"申报或行政材料"}
    if len(rel.parts) == 1 and row["extension"] == ".pdf":
        return bool(re.search(r"endogenous innovation|内生性创新|内源性创新|数字社会创新|社会数字创新|新能源车产业|科技强国", row["filename"], re.I))
    return row["extension"] in {".docx", ".pdf", ".pptx"} and row["probable_document_role"] not in {
        "学术文献或文献综述", "政策新闻案例或机构材料", "申报或行政材料"
    }


def group_versions(rows: list[dict]) -> list[list[dict]]:
    candidates = [r for r in rows if is_project_manuscript(r)]
    parent = list(range(len(candidates)))
    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i
    def union(i, j):
        ri, rj = find(i), find(j)
        if ri != rj:
            parent[rj] = ri
    for i, row in enumerate(candidates):
        key = family_key(row)
        for j in range(i):
            other_key = family_key(candidates[j])
            name_sim = similarity(key, other_key)
            if name_sim >= 0.70 or (min(len(key), len(other_key)) >= 10 and (key in other_key or other_key in key)):
                union(i, j)
    grouped = defaultdict(list)
    for i, row in enumerate(candidates):
        grouped[find(i)].append(row)
    return [g for g in grouped.values() if len(g) > 1]


def build_version_rows(groups: list[list[dict]]) -> list[dict]:
    out = []
    for i, group in enumerate(sorted(groups, key=lambda g: family_key(g[0])), 1):
        family = family_key(group[0]) or f"family_{i}"
        group_sorted = sorted(group, key=lambda r: r["filesystem_modified_time"])
        for row in group_sorted:
            marker = version_marker(row["filename"], row["has_track_changes_if_detectable"])
            candidate = "false"
            reason = "No unique authority assigned."
            if row is group_sorted[-1] and "backup" not in marker and "abandoned" not in marker and row["has_track_changes_if_detectable"] != "true":
                candidate = "true"
                reason = "Candidate only: latest filesystem modification within inferred family and not marked backup/abandoned/track-changes; requires content and provenance review."
            out.append({
                "relationship_id": f"ver_{i:04d}", "document_family": family,
                "file_id": row["file_id"], "source_path": row["original_absolute_path"],
                "filename": row["filename"], "extension": row["extension"],
                "version_marker": marker, "track_changes_status": row["has_track_changes_if_detectable"],
                "relationship_type": "inferred_version_family",
                "related_file_ids": ";".join(r["file_id"] for r in group if r is not row),
                "candidate_authoritative_version": candidate, "candidate_reason": reason,
                "confidence": "high" if similarity(family_key(group[0]), family_key(row)) >= 0.86 else "medium",
                "requires_human_review": "true",
            })
    return out


def build_pairs(rows: list[dict]) -> list[dict]:
    docx = [r for r in rows if r["extension"] == ".docx"]
    pdfs = [r for r in rows if r["extension"] == ".pdf"]
    candidates = []
    for d in docx:
        for p in pdfs:
            stem_sim = similarity(norm(d["filename"]), norm(p["filename"]))
            title_sim = similarity(norm(d.get("document_title", "")), norm(p.get("document_title", "")))
            exact_stem = Path(d["filename"]).stem.casefold() == Path(p["filename"]).stem.casefold()
            score = max(stem_sim, title_sim, 1.0 if exact_stem else 0.0)
            if score >= 0.78:
                candidates.append((score, exact_stem, d, p, stem_sim, title_sim))
    candidates.sort(key=lambda x: (-x[0], not x[1], x[2]["filename"], x[3]["filename"]))
    used_d, used_p, out = set(), set(), []
    for score, exact_stem, d, p, stem_sim, title_sim in candidates:
        if d["file_id"] in used_d or p["file_id"] in used_p:
            continue
        used_d.add(d["file_id"]); used_p.add(p["file_id"])
        out.append({
            "pair_id": f"pair_{len(out)+1:04d}", "docx_file_id": d["file_id"], "pdf_file_id": p["file_id"],
            "docx_path": d["original_absolute_path"], "pdf_path": p["original_absolute_path"],
            "pair_type": "DOCX_PDF_release_or_export_pair",
            "matching_basis": "exact basename" if exact_stem else f"normalised filename/title similarity={score:.3f}",
            "confidence": "high" if exact_stem or score >= 0.92 else "medium",
            "requires_human_review": "false" if exact_stem else "true",
        })
    return out


def build_duplicates(rows: list[dict]) -> list[dict]:
    out = []
    for i, a in enumerate(rows):
        for b in rows[i + 1:]:
            exact = a["sha256"] == b["sha256"]
            name_sim = similarity(norm(a["filename"]), norm(b["filename"]))
            size_a, size_b = int(a["size_bytes"]), int(b["size_bytes"])
            size_ratio = min(size_a, size_b) / max(size_a, size_b) if max(size_a, size_b) else 1.0
            content_sim = 0.0
            if not exact and a["extension"] == b["extension"] and size_ratio >= 0.45 and name_sim >= 0.55:
                content_sim = similarity(text_signature(a)[:12000], text_signature(b)[:12000])
            near = not exact and a["extension"] == b["extension"] and size_ratio >= 0.55 and (name_sim >= 0.78 or content_sim >= 0.82)
            if not exact and not near:
                continue
            rtype = "exact_sha256_duplicate" if exact else "near_duplicate_or_historical_version"
            out.append({
                "relationship_id": f"dup_{len(out)+1:05d}", "file_id_a": a["file_id"], "file_id_b": b["file_id"],
                "path_a": a["original_absolute_path"], "path_b": b["original_absolute_path"],
                "relationship_type": rtype, "sha256_equal": str(exact).lower(),
                "filename_similarity": f"{name_sim:.3f}", "content_similarity": f"{content_sim:.3f}",
                "size_ratio": f"{size_ratio:.3f}",
                "reason": "Byte-identical SHA-256; both entities retained." if exact else "High filename/content similarity with comparable size; preserve as potentially independent history.",
                "confidence": "high" if exact or (name_sim >= 0.9 and content_sim >= 0.9) else "medium",
                "independent_historical_significance": "unknown" if exact else "possible",
                "requires_human_review": "true",
            })
    return out


def build_components(rows: list[dict], version_rows: list[dict]) -> list[dict]:
    projects = [r for r in rows if is_project_manuscript(r)]
    version_family = {r["file_id"]: r["relationship_id"] for r in version_rows}
    out, seen = [], set()
    for parent in projects:
        parent_text = (norm(parent["filename"]) + " " + norm(parent.get("document_title", ""))).strip()
        parent_words = int(parent["word_count_if_available"] or 0) if (parent["word_count_if_available"] or "").isdigit() else 0
        parent_pages = int(parent["page_count"] or 0) if (parent["page_count"] or "").isdigit() else 0
        if parent_words < 5000 and parent_pages < 20:
            continue
        for child in projects:
            if child is parent or child["file_id"] == parent["file_id"]:
                continue
            if version_family.get(parent["file_id"]) and version_family.get(parent["file_id"]) == version_family.get(child["file_id"]):
                continue
            if child["probable_project_theme"] != parent["probable_project_theme"]:
                continue
            if int(child["size_bytes"]) >= int(parent["size_bytes"]) * 0.67:
                continue
            child_text = (norm(child["filename"]) + " " + norm(child.get("document_title", ""))).strip()
            sim = similarity(parent_text, child_text)
            shared = set(parent_text.split()) & set(child_text.split())
            if sim < 0.58 and len(shared) < 4:
                continue
            key = (parent["file_id"], child["file_id"])
            if key in seen:
                continue
            seen.add(key)
            out.append({
                "relationship_id": f"comp_{len(out)+1:04d}", "parent_file_id": parent["file_id"],
                "component_file_id": child["file_id"], "parent_path": parent["original_absolute_path"],
                "component_path": child["original_absolute_path"], "relationship_type": "possible_full_document_component",
                "relationship_reason": f"Shared title/theme tokens and smaller component size; title similarity={sim:.3f}.",
                "confidence": "medium" if sim >= 0.62 else "low", "requires_human_review": "true",
            })
    return out


def report_versions(version_rows: list[dict]) -> str:
    groups = defaultdict(list)
    for r in version_rows:
        groups[r["relationship_id"]].append(r)
    lines = ["# Version history report", "", f"Generated: {now_iso()}", "", "No file is designated as the unique authoritative version. Candidate labels are review prompts only.", ""]
    for rel, group in groups.items():
        lines += [f"## {group[0]['document_family']}", ""]
        for r in sorted(group, key=lambda x: x["filename"]):
            cand = " — **candidate only**" if r["candidate_authoritative_version"] == "true" else ""
            lines.append(f"- `{r['filename']}` ({r['version_marker']}, track changes: {r['track_changes_status']}){cand}")
        lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.parse_args()
    config = load_config()
    rows = read_csv(workspace_path(config["inventory_csv"]))
    groups = group_versions(rows)
    versions = build_version_rows(groups)
    pairs = build_pairs(rows)
    dups = build_duplicates(rows)
    components = build_components(rows, versions)
    class_dir = CONTROL_DIR / "classification"
    write_csv(class_dir / "VERSION_RELATIONSHIP_MAP.csv", versions, VERSION_FIELDS)
    write_csv(class_dir / "COMPONENT_RELATIONSHIP_MAP.csv", components, COMPONENT_FIELDS)
    write_csv(class_dir / "DOCX_PDF_PAIR_MAP.csv", pairs, PAIR_FIELDS)
    write_csv(class_dir / "DUPLICATE_AND_NEAR_DUPLICATE_MAP.csv", dups, DUP_FIELDS)
    reports = CONTROL_DIR / "reports"
    (reports / "VERSION_HISTORY_REPORT.md").write_text(report_versions(versions), encoding="utf-8")
    branch_lines = ["# Project branch report", "", f"Generated: {now_iso()}", "", "## Inferred branches", ""]
    theme_counts = defaultdict(int)
    for r in rows:
        theme_counts[r["probable_project_theme"]] += 1
    for theme, count in sorted(theme_counts.items(), key=lambda x: (-x[1], x[0])):
        branch_lines.append(f"- **{theme}**: {count} files")
    branch_lines += ["", "## Cross-branch observations", "", f"- Inferred version families: {len(groups)}", f"- DOCX/PDF pairs: {len(pairs)}", f"- Possible full-document/component relationships: {len(components)}", f"- Exact and near-duplicate pair records: {len(dups)}", "", "All branch and relationship assignments are provisional; medium/low-confidence records require human review."]
    (reports / "PROJECT_BRANCH_REPORT.md").write_text("\n".join(branch_lines) + "\n", encoding="utf-8")
    (CONTROL_DIR / "logs" / "02_build_relationships.log").write_text(json.dumps({"generated": now_iso(), "version_families": len(groups), "version_rows": len(versions), "pairs": len(pairs), "components": len(components), "duplicate_pairs": len(dups)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"version_families": len(groups), "version_rows": len(versions), "pairs": len(pairs), "components": len(components), "duplicate_pairs": len(dups)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
