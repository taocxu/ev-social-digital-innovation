# EV, Social Digital Innovation, and Endogenous Innovation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Repository**: `taocxu/ev-social-digital-innovation`

## Overview

This repository provides a **research file governance toolkit** and selected **final research outputs** on social and digital innovation in the electric vehicle (EV) industry.

### Repository Contents

| Component | Location | Description |
|-----------|----------|-------------|
| Governance tooling | `control/scripts/` | Reusable file inventory, classification, version-tracking, and integrity-verification scripts |
| Public research outputs | `research_outputs/` | Curated final manuscripts and presentations (PDF, DOCX, PPTX) |
| Configuration and rules | `.gitignore`, `AGENTS.md`, `PUBLIC_RESEARCH_OUTPUT_SELECTION.md` | Repository governance and public release criteria |

### Research Outputs

The following final research outputs are available under `research_outputs/`:

| Topic | File | Format |
|-------|------|--------|
| Endogenous Innovation in the Tech Cold War Era | [Endogenous_Innovation_in_the_Tech_Cold_War_Era.pdf](research_outputs/endogenous_innovation_tech_cold_war/Endogenous_Innovation_in_the_Tech_Cold_War_Era.pdf) | Full manuscript, PDF |
| Technological Sovereignty and Enterprise Innovation | [科技强国视角下的企业内生性创新_01DecV3.pdf](research_outputs/final_manuscripts/科技强国视角下的企业内生性创新_01DecV3.pdf) | Full manuscript, PDF |

Selection criteria: final clean versions only, no track changes, author-finalised or clean releases. PDF is the preferred public reading format.

Intermediate drafts, tracked-changes versions, external references, and internal management records are **not** included.

### Research File Governance Toolkit

The scripts under `control/scripts/` support a reproducible workflow for:

- **Read-only file inventory** — recursive scanning with SHA-256
- **Metadata and document relationship identification** — version families, DOCX/PDF pairs, duplicate detection
- **Target-path collision checking** — Windows filename rules, path-length gates
- **Copy-based reorganisation** — dry-run default, SHA-256 post-copy verification
- **Source retirement audit** — safe-to-delete assessment

**Important**: These tools default to read-only and dry-run mode. They do not delete or modify source files. Always run in dry-run mode first and back up your data before executing any reorganisation.

## Repository Status

- **Visibility**: PRIVATE (will be reviewed for public release after full audit)
- This repository contains **no external copyrighted materials**, **no raw datasets**, **no personal credentials**, and **no full internal audit trails**.
- The complete project audit trail (including full inventories, version maps, and execution logs) is maintained separately.

## License

- **Code** (scripts under `control/scripts/`): Licensed under the [MIT License](LICENSE).
- **Research outputs** (files under `research_outputs/`): All rights reserved by the author(s). These are provided for scholarly reference. No open license is granted by inclusion in this repository.

## Usage

```bash
# Clone the repository
git clone https://github.com/taocxu/ev-social-digital-innovation.git
cd ev-social-digital-innovation

# Run dry-run before any actual operation
python control/scripts/05_verify_reorganisation.py

# See individual script help for details
python control/scripts/02_build_relationships.py --help
```
