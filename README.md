# EV, Social Digital Innovation, and Endogenous Innovation

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Repository**: `taocxu/ev-social-digital-innovation`

## Overview

This repository provides a **research file governance toolkit** and selected **final research outputs** on electric vehicles, social and digital innovation, and endogenous innovation.

## Repository Contents

| Component | Location | Description |
|-----------|----------|-------------|
| Governance tooling | `control/scripts/` | Reusable file classification, version-tracking, and integrity-verification scripts |
| Public research outputs | `research_outputs/` | Curated final manuscripts and reports in PDF or DOCX format |
| References | `references/` | Deduplicated bibliography, selected works, and licence-verified hosted references |
| Configuration and rules | `.gitignore`, `AGENTS.md`, `PUBLIC_RESEARCH_OUTPUT_SELECTION.md` | Repository governance and public-release criteria |

## Research Outputs

| File | Format | Description |
|------|--------|-------------|
| [Endogenous Innovation in the Tech Cold War Era](research_outputs/final_reports/Endogenous_Innovation_in_the_Tech_Cold_War_Era.pdf) | PDF | Endogenous innovation dynamics under technology competition |
| [科技强国视角下的企业内生性创新](research_outputs/final_reports/科技强国视角下的企业内生性创新.pdf) | PDF | Enterprise endogenous innovation from a technological sovereignty perspective |
| [社会数字创新和新能源车产业](research_outputs/final_manuscripts/社会数字创新和新能源车产业_040625.docx) | DOCX | Social digital innovation and the electric vehicle industry |

These files are user-curated final research outputs. Intermediate drafts, tracked-changes versions, process notes, and external copyrighted materials are excluded. PDF is the preferred reading format where available.

## References

1. De Podestá Gomes, A., Pauls, R., & ten Brink, T. (2023). Industrial policy and the creation of the electric vehicles market in China: Demand structure, sectoral complementarities and policy coordination. *Cambridge Journal of Economics, 47*(1), 45–66. https://doi.org/10.1093/cje/beac056  
   [Hosted PDF, CC BY 4.0](references/ev_industry/DePodestaGomes_2023_Industrial_Policy_EV_China.pdf)

2. Xu, T. C. (2025). The road not taken? Industrial policy and political settlements in China and Indonesia, 1990–2022. *SSRN Electronic Journal*. https://doi.org/10.2139/ssrn.5085509

3. Xu, T. L., & Hu, Y. (2024). Towards sustainable prosperity? Policy evaluation of Jiangsu advanced manufacturing clusters. *Technology in Society, 77*, 102583. https://doi.org/10.1016/j.techsoc.2024.102583

4. Xu, T. L., & Liu, L. (2025). Endogenous innovation in the Tech Cold War era (MPRA Paper No. 126220). Munich Personal RePEc Archive. https://mpra.ub.uni-muenchen.de/126220/

5. Xu, T. L., & Zhu, W. (2022). When Polanyi met Schumpeter: Social trust and entrepreneurship (MPRA Paper No. 123894). Munich Personal RePEc Archive. https://mpra.ub.uni-muenchen.de/123894/  
   Latest version deposited in 2025.

The [complete deduplicated bibliography](references/REFERENCES.md) is organised alphabetically and is being progressively standardised against verified DOI and official-source metadata. The [reference curation note](references/BIBLIOGRAPHY_CURATION_NOTE.md) documents the inclusion and deduplication rules.

Only references with clear redistribution licences are hosted as third-party PDFs. Bibliographic entries remain distinct from the repository's original research outputs.

## Repository Status

- **Visibility**: PUBLIC
- This repository contains the author's selected research outputs and a limited set of licence-verified academic references.
- Full project audit trails and internal working materials are maintained separately.

## Licence

- **Code** under `control/scripts/`: Licensed under the [MIT License](LICENSE).
- **Research outputs** under `research_outputs/`: All rights reserved by the author(s). These are provided for scholarly reference; no open licence is granted by their inclusion in this repository.
- **Third-party references** under `references/`: Governed by the licence stated for each hosted item. The repository's MIT licence does not apply to them.

## Usage

```bash
# Clone the repository
git clone https://github.com/taocxu/ev-social-digital-innovation.git
cd ev-social-digital-innovation

# See individual script help for available options
python control/scripts/02_build_relationships.py --help
```

Run all file-governance tools in dry-run mode before any filesystem operation. Review each script's help and configuration requirements before execution.
