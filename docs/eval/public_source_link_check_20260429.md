# 外部公开来源链接健康检查报告

- generated_at: `2026-05-01T01:56:59.629895+00:00`
- seed_path: `D:\newwork\lab-safe-assistant-dify-rag\data_sources\public_lab_safety_sources_v1.csv`
- external_csv: `D:\newwork\lab-safe-assistant-dify-rag\release_exports\v10_external_sources\knowledge_base_external_import_ready.csv`
- source_count: `73`
- external_rows: `1159`
- status_counts: `{'cached_ok_live_failed': 1, 'ok': 72}`
- bad_link_count: `0`
- zero_generated_rows_count: `5`
- ok_but_zero_generated_rows_count: `5`

## 结论口径

- `status=ok` 表示链接当前可访问且返回非空内容。
- `status=cached_ok_live_failed` 表示实时访问受到临时反爬/远端断开影响，但本地已保存原始抓取物和抽取文本，且已生成知识条目；这类不按死链处理，但应在提交前择时复查。
- `generated_rows=0` 不一定是链接坏，可能是 PDF 海报/短通知/图片型 PDF 导致文本不足或抽取质量低。
- 验收应优先采用 `status=ok 且 generated_rows>0` 的来源；`cached_ok_live_failed` 可作为已有抓取证据来源但需复查实时可访问性；0 条来源可保留为抓取证据，但不计入有效知识条目贡献。

## 问题链接

| id | status | http | rows | content_type | url | error |
|---|---|---:|---:|---|---|---|
| 无 | - | - | - | - | - | - |

## 可访问但未生成条目的来源

| id | http | content_type | sampled_bytes | url | 处理建议 |
|---|---:|---|---:|---|---|
| YALE-HF | 200 | application/pdf | 65536 | https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |
| YALE-LAB-RULES | 200 | application/pdf | 65536 | https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |
| YALE-MIN-PPE | 200 | application/pdf | 65536 | https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |
| YALE-NEEDLEBOX | 200 | application/pdf | 65536 | https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |
| YALE-UNATTENDED | 200 | application/pdf | 54376 | https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf | 检查是否为短海报/图片型PDF；若不能稳定抽取文本，则从有效来源清单剔除或保留为附属证据 |

## 全量链接检查明细

| id | org | status | http | rows | content_type | url |
|---|---|---|---:|---:|---|---|
| OSHA-1910-1450 | OSHA | cached_ok_live_failed | 403 | 6 | text/html | https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450 |
| NIH-CSG | NIH Office of Research Services | ok | 200 | 66 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/chemical-safety-guide.pdf |
| NIH-CHP | NIH Office of Research Services | ok | 200 | 80 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/chemical-hygiene-plan.pdf |
| NIH-SEG | NIH Office of Research Services | ok | 200 | 17 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/chemical-segregation-and-storage.pdf |
| NIH-GAS-CRYO | NIH Office of Research Services | ok | 200 | 24 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf |
| NIH-PEROXIDE | NIH Office of Research Services | ok | 200 | 10 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/managing-peroxide-formers-in-the-lab.pdf |
| NIH-PYRO | NIH Office of Research Services | ok | 200 | 18 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/managing-pyrophoric-and-water-reactive-chemicals-in-the-laboratories.pdf |
| NIH-COMPAT-STORAGE | NIH Office of Research Services | ok | 200 | 3 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-compatible-chemical-storage.pdf |
| NIH-CABINET | NIH Office of Research Services | ok | 200 | 6 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-chemical-storage-cabinets.pdf |
| NIH-CRYOGEN-FS | NIH Office of Research Services | ok | 200 | 5 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/cryogen-fact-sheet.pdf |
| NIH-PHS | NIH Office of Research Services | ok | 200 | 9 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/particularly-hazardous-substances-phs.pdf |
| NIH-DCM | NIH Office of Research Services | ok | 200 | 7 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/working-safely-with-dichloromethane.pdf |
| NIH-DCM-PLAN | NIH Office of Research Services | ok | 200 | 18 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/nih-dichloromethane-health-and-safety-plan.pdf |
| NIH-OEL | NIH Office of Research Services | ok | 200 | 4 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/occupational-exposure-limits-for-chemicals.pdf |
| NIH-FUME-HOOD-CLEAN | NIH Office of Research Services | ok | 200 | 8 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/how-to-safely-clean-cfh-web.pdf |
| NIH-LAB-SOP-TEMPLATE | NIH Office of Research Services | ok | 200 | 13 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/lab-specific-sop-template.pdf |
| NIH-TOXIN | NIH Office of Research Services | ok | 200 | 7 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/exempt-toxin-program-requirements.pdf |
| NIH-INACTIVATION | NIH Office of Research Services | ok | 200 | 7 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/inactivation-method-review-process.pdf |
| CDC-BMBL6 | CDC/NIH | ok | 200 | 170 | application/pdf | https://www.cdc.gov/labs/pdf/SF__19_308133-A_BMBL6_00-BOOK-WEB-final-3.pdf |
| NIH-BMBL6 | NIH Office of Research Services | ok | 200 | 80 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/biosafety-in-microbiological-and-biomedical-laboratories.PDF |
| NIH-LASER | NIH Office of Research Services | ok | 200 | 25 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/laser-safety-program.pdf |
| NIH-LABCOAT | NIH Office of Research Services | ok | 200 | 12 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/laboratory-coat-selection-guidance.pdf |
| NIH-ECP | NIH Office of Research Services | ok | 200 | 50 | application/pdf | https://ors.od.nih.gov/sr/dohs/Documents/exposure-control-plan.pdf |
| NCBI-PRUDENT-OVERVIEW | National Academies Press / NCBI Bookshelf | ok | 200 | 43 | text/html; charset=UTF-8 | https://www.ncbi.nlm.nih.gov/books/NBK55873/ |
| NCBI-PRUDENT-GENERAL | National Academies Press / NCBI Bookshelf | ok | 200 | 8 | text/html; charset=UTF-8 | https://www.ncbi.nlm.nih.gov/books/NBK55878/ |
| NCBI-PRUDENT-EQUIPMENT | National Academies Press / NCBI Bookshelf | ok | 200 | 16 | text/html; charset=UTF-8 | https://www.ncbi.nlm.nih.gov/books/NBK55882/ |
| NCBI-PRUDENT-CHEMICAL | National Academies Press / NCBI Bookshelf | ok | 200 | 67 | text/html; charset=UTF-8 | https://www.ncbi.nlm.nih.gov/books/NBK55884/ |
| CORNELL-LSM | Cornell University EHS | ok | 200 | 3 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual |
| CORNELL-CHP | Cornell University EHS | ok | 200 | 13 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/chemical-safety/chemical-hygiene-plan |
| CORNELL-BIOSAFETY-DOCS | Cornell University EHS | ok | 200 | 3 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/biosafety-biosecurity/biological-safety-manuals-and-other-documents |
| CORNELL-TRAINING-MATRIX | Cornell University EHS | ok | 200 | 8 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/general-laboratory-safety/laboratory-safety-training-matrix |
| CORNELL-LASER-PAGE | Cornell University EHS | ok | 200 | 2 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/radiation-safety/laser-safety |
| CORNELL-SDS | Cornell University EHS | ok | 200 | 3 | text/html; charset=UTF-8 | https://ehs.cornell.edu/research-safety/chemical-safety/safety-data-sheets-chemwatch |
| CORNELL-HW-MANUAL | Cornell University EHS | ok | 200 | 79 | text/html; charset=UTF-8 | https://ehs.cornell.edu/book/export/html/1261 |
| YALE-CHP | Yale Environmental Health & Safety | ok | 200 | 80 | application/pdf | https://ehs.yale.edu/sites/default/files/files/laboratory-chemical-hygiene-plan.pdf |
| YALE-LASER-SOP | Yale Environmental Health & Safety | ok | 200 | 4 | application/pdf | https://ehs.yale.edu/sites/default/files/files/laser-sop.pdf |
| YALE-HF | Yale Environmental Health & Safety | ok | 200 | 0 | application/pdf | https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf |
| YALE-LAB-RULES | Yale Environmental Health & Safety | ok | 200 | 0 | application/pdf | https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf |
| YALE-MIN-PPE | Yale Environmental Health & Safety | ok | 200 | 0 | application/pdf | https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf |
| YALE-BSC-POSTER | Yale Environmental Health & Safety | ok | 200 | 1 | application/pdf | https://ehs.yale.edu/sites/default/files/files/biosafety-cabinet-poster.pdf |
| YALE-NEEDLEBOX | Yale Environmental Health & Safety | ok | 200 | 0 | application/pdf | https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf |
| YALE-WASTE-PLACE | Yale Environmental Health & Safety | ok | 200 | 2 | application/pdf | https://ehs.yale.edu/sites/default/files/files/waste-in-place.pdf |
| YALE-FUME-HOOD-NOTICE | Yale Environmental Health & Safety | ok | 200 | 3 | application/pdf | https://ehs.yale.edu/sites/default/files/files/fume-hood-repair-notice.pdf |
| YALE-UNATTENDED | Yale Environmental Health & Safety | ok | 200 | 0 | application/pdf | https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf |
| YALE-CHEM-APPROVAL | Yale Environmental Health & Safety | ok | 200 | 8 | application/pdf | https://ehs.yale.edu/sites/default/files/files/chemicals-ehs-approval.pdf |
| YALE-GENE-DRIVE | Yale Environmental Health & Safety | ok | 200 | 8 | application/pdf | https://ehs.yale.edu/sites/default/files/files/gene-drive-modified-organisms.pdf |
| YALE-PPE-LABS | Yale Environmental Health & Safety | ok | 200 | 10 | application/pdf | https://ehs.yale.edu/sites/default/files/files/ppe-procedure-labs.pdf |
| YALE-SHOP-GUIDE | Yale Environmental Health & Safety | ok | 200 | 7 | text/html; charset=utf-8 | https://ehs.yale.edu/shop-tool-safety |
| YALE-STUDENT-SHOP | Yale Environmental Health & Safety | ok | 200 | 3 | application/pdf | https://ehs.yale.edu/sites/default/files/files/student-shop-rules.pdf |
| YALE-ART-SAFETY | Yale Environmental Health & Safety | ok | 200 | 9 | text/html; charset=utf-8 | https://ehs.yale.edu/art-safety |
| BERKELEY-CHP | UC Berkeley Office of Environment, Health & Safety | ok | 200 | 7 | text/html; charset=utf-8 | https://ehs.berkeley.edu/safety-subjects/chemical-safety/chemical-hygiene-plan |
| BERKELEY-LSM | UC Berkeley Office of Environment, Health & Safety | ok | 200 | 7 | text/html; charset=utf-8 | https://ehs.berkeley.edu/laboratory-safety-manual |
| BERKELEY-BIOSAFETY | UC Berkeley Office of Environment, Health & Safety | ok | 200 | 1 | text/html; charset=utf-8 | https://ehs.berkeley.edu/publications/biological-safety-program-manual |
| BERKELEY-LASER | UC Berkeley Office of Environment, Health & Safety | ok | 200 | 1 | text/html; charset=utf-8 | https://ehs.berkeley.edu/laser-safety-manual |
| MIT-CHEMICAL | MIT Environment, Health & Safety | ok | 200 | 3 | text/html; charset=UTF-8 | https://ehs.mit.edu/chemical-safety/ |
| MIT-CHEM-HYGIENE | MIT Environment, Health & Safety | ok | 200 | 6 | text/html; charset=UTF-8 | https://ehs.mit.edu/chemical-safety-program/chemical-hygiene/ |
| STANFORD-CHEM-TOOLKIT | Stanford Environmental Health & Safety | ok | 200 | 1 | text/html; charset=UTF-8 | https://ehs.stanford.edu/forms-tools/laboratory-chemical-safety-toolkit |
| STANFORD-CHEM-WASTE | Stanford Environmental Health & Safety | ok | 200 | 4 | text/html; charset=UTF-8 | https://ehs.stanford.edu/topic/chemical-safety/chemical-waste-disposal |
| STANFORD-BIO-WASTE | Stanford Environmental Health & Safety | ok | 200 | 5 | text/html; charset=UTF-8 | https://ehs.stanford.edu/manual/biosafety-manual/waste |
| STANFORD-FUME-HOOD | Stanford Environmental Health & Safety | ok | 200 | 1 | text/html; charset=UTF-8 | https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/fume-hood-location |
| PRINCETON-CHEM-WASTE | Princeton Environmental Health and Safety | ok | 200 | 1 | text/html; charset=UTF-8 | https://ehs.princeton.edu/laboratory-research/chemical-waste-management |
| UW-CHEM-SAFETY | University of Washington Environmental Health & Safety | ok | 200 | 5 | text/html; charset=UTF-8 | https://www.ehs.washington.edu/chemical/chemical-safety |
| UW-CHEM-WASTE | University of Washington Environmental Health & Safety | ok | 200 | 13 | text/html; charset=UTF-8 | https://www.ehs.washington.edu/chemical/chemical-waste |
| UW-BIO-WASTE | University of Washington Environmental Health & Safety | ok | 200 | 9 | text/html; charset=UTF-8 | https://www.ehs.washington.edu/biological/biohazardous-waste |
| UW-FUME-HOODS | University of Washington Environmental Health & Safety | ok | 200 | 8 | text/html; charset=UTF-8 | https://www.ehs.washington.edu/research-lab/fume-hoods-use-inspection-and-maintenance |
| UCSD-FUME-HOODS | UC San Diego Blink | ok | 200 | 6 | text/html; charset=UTF-8 | https://blink.ucsd.edu/safety/research-lab/chemical/hoods/ |
| UCSD-EXTREME-WASTE | UC San Diego Blink | ok | 200 | 14 | text/html; charset=UTF-8 | https://blink.ucsd.edu/safety/research-lab/hazardous-waste/disposal-guidance/extremely.html |
| UTEXAS-FUME-HOODS | UT Austin Environmental Health & Safety | ok | 200 | 7 | text/html; charset=UTF-8 | https://ehs.utexas.edu/working-safely/equipment-safety/fume-hoods |
| UTEXAS-CHEM-WASTE | UT Austin Environmental Health & Safety | ok | 200 | 23 | text/html; charset=UTF-8 | https://ehs.utexas.edu/environment-waste/waste-management/chemical-waste |
| NCSU-FUME-HOODS | NC State Environmental Health and Safety | ok | 200 | 1 | text/html; charset=UTF-8 | https://ehs.ncsu.edu/laboratory/fume-hoods/ |
| NCSU-LAB-SECURITY | NC State Environmental Health and Safety | ok | 200 | 3 | text/html; charset=UTF-8 | https://ehs.ncsu.edu/laboratory-safety/laboratory-security-and-safety-guidelines/ |
| NCSU-CHEM-HAZARDS | NC State Environmental Health and Safety | ok | 200 | 1 | text/html; charset=UTF-8 | https://ehs.ncsu.edu/laboratory-safety/secondary-safety-contact/chemical-hazards-ssc/ |
| NCSU-CHEM-WASTE | NC State Environmental Health and Safety | ok | 200 | 7 | text/html; charset=UTF-8 | https://ehs.ncsu.edu/home-page-info/environmental-affairs/chemical-waste/ |