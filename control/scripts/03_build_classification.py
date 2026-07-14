from __future__ import annotations

import argparse
import json
import re
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from common import CONTROL_DIR, human_bytes, load_config, now_iso, read_csv, workspace_path, write_csv

FIELDS = [
    "file_id", "source_path", "original_filename", "proposed_target_relative_path",
    "proposed_target_filename", "project_theme", "document_family", "document_role",
    "material_type", "version_status", "paired_file_id", "related_component_ids",
    "classification_reason", "confidence", "requires_human_review", "collision_risk", "copy_action",
]
UNRESOLVED_FIELDS = [
    "file_id", "source_path", "original_filename", "proposed_fallback_path", "reason",
    "confidence", "requires_human_review", "recommended_review_question",
]
COLLISION_FIELDS = [
    "collision_id", "proposed_target_relative_path", "file_ids", "source_paths", "filenames",
    "collision_type", "required_action", "blocks_execution",
]


def classify_material(row: dict) -> str:
    ext = row["extension"]
    if ext in {".dta", ".sav", ".sas7bdat", ".parquet"}: return "dataset"
    if ext in {".xlsx", ".xls", ".csv"}: return "spreadsheet_or_data"
    if ext in {".do", ".py", ".r", ".ipynb", ".m"}: return "code"
    if ext in {".pptx", ".ppt"}: return "presentation"
    if ext in {".png", ".jpg", ".jpeg", ".svg", ".emf", ".eps", ".eddx", ".drawio"}: return "figure_or_editable_source"
    if ext == ".pdf": return "pdf"
    if ext == ".docx": return "word_document"
    if ext == ".lnk": return "shortcut"
    return "other"


def version_status(row: dict) -> str:
    name = row["filename"].casefold()
    if row["office_temp_file"] == "true": return "office_temporary"
    if re.search(r"废案|abandon", name): return "abandoned_but_retained"
    if re.search(r"留痕|track", name) or row["has_track_changes_if_detectable"] == "true": return "track_changes"
    if re.search(r"备份|backup|copy", name): return "backup"
    if re.search(r"提交|submission|submit", name): return "submission_labelled"
    if re.search(r"draft|草稿", name): return "draft"
    if re.search(r"final|最终|定稿", name): return "final_label_unverified"
    if re.search(r"v\s*\d+(?:\.\d+)*|\d{4,8}", name): return "dated_or_numbered_version"
    return "unmarked_version"


def theme_subdir(theme: str, literature: bool = False) -> str:
    if "EV产业" in theme:
        return "01_EV和新能源汽车产业" if literature else "04_EV产业研究"
    if "社会数字创新" in theme:
        return "03_社会创新和数字创新" if literature else "05_社会数字创新研究"
    if "内生性创新" in theme:
        return "04_内生创新和技术进步" if literature else "06_内生性创新研究"
    return "99_待进一步分类" if literature else "99_待人工判断"


def target_dir(row: dict, status: str) -> tuple[str, str, str]:
    role, ext, theme = row["probable_document_role"], row["extension"], row["probable_project_theme"]
    name = row["filename"].casefold()
    if row["office_temp_file"] == "true":
        return "99_待人工判断", "Office temporary file is recorded but excluded from formal copying.", "high"
    if role == "快捷方式":
        return "12_协作_反馈和修改过程/05_待确认版本", "Shortcut target was not treated as an independent authoritative research file; manual target review required.", "low"
    if role == "申报或行政材料" or "评奖申报" in theme:
        if re.search(r"通知|要求|办法", name): sub = "01_通知和要求"
        elif re.search(r"申报|填写|承诺", name): sub = "02_申报表和承诺材料"
        elif re.search(r"清单|目录", name): sub = "03_提交清单"
        elif re.search(r"证明|附件|依托材料", name): sub = "04_证明和附件"
        else: sub = "05_往来和管理记录"
        return f"02_评奖申报和行政材料/{sub}", "Award/application and administrative content separated from academic material.", "high"
    if ext in {".dta", ".sav", ".sas7bdat", ".parquet"}:
        return "08_数据_代码和实证结果/01_原始数据", "Dataset classified by file type; raw/intermediate status remains reviewable.", "medium"
    if ext in {".do", ".py", ".r", ".ipynb", ".m"}:
        return "08_数据_代码和实证结果/03_代码", "Code classified by file type.", "high"
    if ext in {".xlsx", ".xls", ".csv"}:
        if "文献" in name:
            return "09_学术文献库/99_待进一步分类", "Spreadsheet appears to index literature; thematic allocation requires review.", "medium"
        return "08_数据_代码和实证结果/05_表格", "Spreadsheet/data table classified by file type and detected role.", "medium"
    if ext in {".pptx", ".ppt"}:
        sub = "01_当前PPT" if not re.search(r"历史|旧|v\d|\d{4,8}", name) else "02_历史PPT"
        return f"11_PPT_图表和可编辑源文件/{sub}", "Presentation classified separately from manuscript files; current status remains provisional.", "medium"
    if ext in {".png", ".jpg", ".jpeg", ".svg", ".emf", ".eps", ".eddx", ".drawio"}:
        sub = "03_图表源文件" if ext in {".eddx", ".drawio", ".svg", ".emf", ".eps"} else "04_图片导出"
        return f"11_PPT_图表和可编辑源文件/{sub}", "Image/source file separated from presentations and prose.", "medium"
    if role == "学术文献或文献综述":
        return f"09_学术文献库/{theme_subdir(theme, True)}", "Academic literature separated from policy/news/institutional material; theme inferred from title and extracted text.", "high" if theme != "待判断" else "low"
    if role == "政策新闻案例或机构材料":
        if "上海" in row["filename"]: sub = "02_上海和地方政策"
        elif re.search(r"政策|战略|政府|十四五", row["filename"]): sub = "01_国家政策"
        elif re.search(r"公司|企业|上汽|合肥", row["filename"]): sub = "03_企业案例"
        elif re.search(r"产业|汽车|创新", row["filename"]): sub = "04_产业案例"
        else: sub = "06_机构报告"
        return f"10_新闻_案例_政策和机构材料/{sub}", "Policy, case, news or institutional evidence separated from academic literature.", "medium"
    if role in {"研究报告论文或章节", "修改痕迹或协作版本"}:
        if status == "track_changes":
            return "12_协作_反馈和修改过程/02_修改痕迹", "Detected or labelled track-changes version.", "high"
        if status == "abandoned_but_retained":
            return "13_过程材料和历史废案/05_废案但保留", "Explicitly labelled abandoned draft; retained without deletion.", "high"
        if re.search(r"工作留痕|参考文献|references|术语|手册", name):
            return "13_过程材料和历史废案/03_研究笔记", "Working record, references component or writing manual rather than a complete report.", "medium"
        word_count = int(row["word_count_if_available"] or 0) if (row["word_count_if_available"] or "").isdigit() else 0
        pages = int(row["page_count"] or 0) if (row["page_count"] or "").isdigit() else 0
        complete = word_count >= 5000 or pages >= 20 or re.search(r"科技强国视角下|tech cold war era|协同发展研究", name)
        if complete:
            if status == "submission_labelled": sub = "06_提交发布包"
            elif ext == ".pdf": sub = "05_PDF导出"
            elif status in {"backup", "dated_or_numbered_version", "draft", "final_label_unverified"}: sub = "02_历史版本"
            else: sub = "01_作者清洁版本"
            return f"03_完整报告和论文版本/{sub}", "Length/title indicates a complete report or paper; version labels do not establish authority.", "medium"
        base = theme_subdir(theme, False)
        if base == "99_待人工判断":
            return base, "Insufficient evidence for reliable thematic and functional classification.", "low"
        sub = "01_章节和正文组件"
        if re.search(r"提纲|框架|理论|概念", name): sub = "02_理论和研究笔记"
        if "综合_" in theme: return "07_综合理论框架/03_三主题连接机制", "Cross-theme prose component inferred from title and extracted text.", "medium"
        return f"{base}/{sub}", "Shorter project prose classified as a thematic chapter/component rather than a complete report.", "medium"
    if ext in {".docx", ".pdf"}:
        return "99_待人工判断", "Document was parsed, but evidence was insufficient to distinguish project prose, literature, or supporting material reliably.", "low"
    return "99_待人工判断", "No reliable rule matched the file.", "low"


def main() -> int:
    argparse.ArgumentParser().parse_args()
    config = load_config()
    inventory = read_csv(workspace_path(config["inventory_csv"]))
    versions = read_csv(CONTROL_DIR / "classification" / "VERSION_RELATIONSHIP_MAP.csv")
    pairs = read_csv(CONTROL_DIR / "classification" / "DOCX_PDF_PAIR_MAP.csv")
    components = read_csv(CONTROL_DIR / "classification" / "COMPONENT_RELATIONSHIP_MAP.csv")
    family_by_id = {r["file_id"]: r["document_family"] for r in versions}
    paired = {}
    for r in pairs:
        paired[r["docx_file_id"]] = r["pdf_file_id"]
        paired[r["pdf_file_id"]] = r["docx_file_id"]
    related = defaultdict(set)
    for r in components:
        related[r["parent_file_id"]].add(r["component_file_id"])
        related[r["component_file_id"]].add(r["parent_file_id"])

    out = []
    for row in inventory:
        status = version_status(row)
        directory, reason, confidence = target_dir(row, status)
        target_rel = str(PurePosixPath(directory) / row["filename"])
        out.append({
            "file_id": row["file_id"], "source_path": row["original_absolute_path"],
            "original_filename": row["filename"], "proposed_target_relative_path": target_rel,
            "proposed_target_filename": row["filename"], "project_theme": row["probable_project_theme"],
            "document_family": family_by_id.get(row["file_id"], ""), "document_role": row["probable_document_role"],
            "material_type": classify_material(row), "version_status": status,
            "paired_file_id": paired.get(row["file_id"], ""),
            "related_component_ids": ";".join(sorted(related[row["file_id"]])),
            "classification_reason": reason, "confidence": confidence,
            "requires_human_review": str(confidence in {"medium", "low"}).lower(),
            "collision_risk": "false", "copy_action": "record_only_office_temp" if status == "office_temporary" else "copy",
        })

    collisions_by_path = defaultdict(list)
    for r in out:
        collisions_by_path[r["proposed_target_relative_path"].casefold()].append(r)
    collisions = []
    for key, group in collisions_by_path.items():
        if len(group) < 2:
            continue
        for r in group:
            r["collision_risk"] = "true"
        collisions.append({
            "collision_id": f"collision_{len(collisions)+1:04d}",
            "proposed_target_relative_path": group[0]["proposed_target_relative_path"],
            "file_ids": ";".join(r["file_id"] for r in group),
            "source_paths": ";".join(r["source_path"] for r in group),
            "filenames": ";".join(r["original_filename"] for r in group),
            "collision_type": "multiple_sources_same_proposed_target",
            "required_action": "Human-approved target rename or directory distinction before execution; no overwrite permitted.",
            "blocks_execution": "true",
        })

    unresolved = []
    for r in out:
        if r["requires_human_review"] == "true" or r["collision_risk"] == "true":
            unresolved.append({
                "file_id": r["file_id"], "source_path": r["source_path"], "original_filename": r["original_filename"],
                "proposed_fallback_path": r["proposed_target_relative_path"],
                "reason": r["classification_reason"] + (" Target-name collision also requires resolution." if r["collision_risk"] == "true" else ""),
                "confidence": r["confidence"], "requires_human_review": "true",
                "recommended_review_question": "Confirm document identity, version status, and sole primary target location.",
            })

    class_dir = CONTROL_DIR / "classification"
    write_csv(class_dir / "CLASSIFICATION_MAP.csv", out, FIELDS)
    write_csv(class_dir / "UNRESOLVED_FILES.csv", unresolved, UNRESOLVED_FIELDS)
    write_csv(class_dir / "NAME_COLLISIONS.csv", collisions, COLLISION_FIELDS)

    used_dirs = Counter(str(PurePosixPath(r["proposed_target_relative_path"]).parent) for r in out)
    structure = ["# Proposed target structure", "", f"Generated: {now_iso()}", "", "The formal `_REORG` directory has **not** been created. Only directories that would receive at least one inventoried entity are listed.", "", "```text"]
    for directory, count in sorted(used_dirs.items()):
        structure.append(f"{directory}/  [{count} files]")
    structure += ["```", "", "`01_当前权威版本` is intentionally not populated at this stage because no unique authoritative version has been approved."]
    (CONTROL_DIR / "reports" / "PROPOSED_TARGET_STRUCTURE.md").write_text("\n".join(structure) + "\n", encoding="utf-8")

    counts = Counter(r["confidence"] for r in out)
    copy_count = sum(r["copy_action"] == "copy" for r in out)
    class_report = ["# Classification report", "", f"Generated: {now_iso()}", "", f"- Classified inventory records: **{len(out)}**", f"- Proposed copy actions: **{copy_count}**", f"- Office temporary records excluded from formal copy: **{sum(r['copy_action'] != 'copy' for r in out)}**", f"- Human-review records: **{len(unresolved)}**", f"- Blocking target-name collisions: **{len(collisions)}**", "", "## Confidence", ""]
    for level in ("high", "medium", "low"):
        class_report.append(f"- {level}: {counts[level]}")
    class_report += ["", "No classification assigns a unique authoritative version. Medium and low confidence records are explicitly flagged for human review."]
    (CONTROL_DIR / "reports" / "CLASSIFICATION_REPORT.md").write_text("\n".join(class_report) + "\n", encoding="utf-8")

    themes = Counter(r["probable_project_theme"] for r in inventory)
    roles = Counter(r["probable_document_role"] for r in inventory)
    version_families = defaultdict(list)
    for r in versions:
        version_families[r["relationship_id"]].append(r["filename"])
    overview = ["# Content overview", "", f"Generated: {now_iso()}", "", "## Overall structure", "", f"The source contains **{len(inventory)} files** totalling **{human_bytes(sum(int(r['size_bytes']) for r in inventory))}**. It combines award application material, project manuscripts, thematic evidence, academic literature, policy/case material, presentations, figures, spreadsheets, shortcuts, and historical working versions.", "", "## Main research themes", ""]
    for theme, count in themes.most_common():
        overview.append(f"- {theme}: {count} files")
    overview += ["", "## Principal reports and manuscript families", ""]
    for _, names in sorted(version_families.items(), key=lambda x: (-len(x[1]), x[1][0]))[:12]:
        overview.append(f"- {len(names)} linked versions: " + "; ".join(f"`{n}`" for n in names[:8]) + ("; …" if len(names) > 8 else ""))
    overview += ["", "## Material groups", ""]
    for role, count in roles.most_common():
        overview.append(f"- {role}: {count} files")
    overview += ["", "## Current structural problems", "", "- Project-authored reports, administrative submissions, literature, policy/case evidence, and working files coexist at the source root.", "- Multiple inferred manuscript version chains use inconsistent date/version conventions; labels such as `final`, dates, or submission wording are not sufficient to establish authority.", "- DOCX/PDF exports, chapter components, shortcuts, exact duplicates, and near-duplicates require explicit relationship tracking.", "- Some materials combine EV industry, digital social innovation, and endogenous innovation and therefore need a single primary location plus cross-indexing.", "- Medium/low-confidence and collision records remain unresolved rather than being forced into a false zero-review state."]
    (CONTROL_DIR / "reports" / "CONTENT_OVERVIEW.md").write_text("\n".join(overview) + "\n", encoding="utf-8")
    (CONTROL_DIR / "logs" / "03_build_classification.log").write_text(json.dumps({"generated": now_iso(), "records": len(out), "copy": copy_count, "human_review": len(unresolved), "collisions": len(collisions), "confidence": dict(counts)}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"records": len(out), "copy": copy_count, "human_review": len(unresolved), "collisions": len(collisions), "confidence": dict(counts)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
