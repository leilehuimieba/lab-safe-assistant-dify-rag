# 外部公开权威实验室安全资料采集报告

- generated_at: `2026-05-01T01:50:07.137495+00:00`
- source_count: `73`
- generated_rows: `1159`
- output_csv: `D:\newwork\lab-safe-assistant-dify-rag\release_exports\v10_external_sources\knowledge_base_external_import_ready.csv`
- seed_csv: `D:\newwork\lab-safe-assistant-dify-rag\data_sources\public_lab_safety_sources_v1.csv`
- raw_artifacts: `D:\newwork\lab-safe-assistant-dify-rag\artifacts\web_ingest_public_20260429`

## 口径说明

本报告对应的是从 OSHA、NIH、CDC/NIH、NCBI Bookshelf 和高校 EHS 等公开权威来源新增采集的数据。
它不同于 `release_exports/v9_original_claim_3000/knowledge_base_import_ready_3000.csv` 的长文档语义切分包；后者只改善检索粒度，不能作为新增独立外部数据来源证明。

## 来源统计

| source_id | org | type | status | extracted_chars | generated_rows | url |
|---|---|---|---:|---:|---:|---|
| OSHA-1910-1450 | OSHA | text/html | ok | 10769 | 6 | https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450 |
| NIH-CSG | NIH Office of Research Services | application/pdf | ok | 63887 | 66 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-safety-guide.pdf |
| NIH-CHP | NIH Office of Research Services | application/pdf | ok | 182641 | 80 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-hygiene-plan.pdf |
| NIH-SEG | NIH Office of Research Services | application/pdf | ok | 12463 | 17 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-segregation-and-storage.pdf |
| NIH-GAS-CRYO | NIH Office of Research Services | application/pdf | ok | 43307 | 24 | https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf |
| NIH-PEROXIDE | NIH Office of Research Services | application/pdf | ok | 6312 | 10 | https://ors.od.nih.gov/sr/dohs/Documents/managing-peroxide-formers-in-the-lab.pdf |
| NIH-PYRO | NIH Office of Research Services | application/pdf | ok | 22659 | 18 | https://ors.od.nih.gov/sr/dohs/Documents/managing-pyrophoric-and-water-reactive-chemicals-in-the-laboratories.pdf |
| NIH-COMPAT-STORAGE | NIH Office of Research Services | application/pdf | ok | 3714 | 3 | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-compatible-chemical-storage.pdf |
| NIH-CABINET | NIH Office of Research Services | application/pdf | ok | 5052 | 6 | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-chemical-storage-cabinets.pdf |
| NIH-CRYOGEN-FS | NIH Office of Research Services | application/pdf | ok | 3691 | 5 | https://ors.od.nih.gov/sr/dohs/Documents/cryogen-fact-sheet.pdf |
| NIH-PHS | NIH Office of Research Services | application/pdf | ok | 7731 | 9 | https://ors.od.nih.gov/sr/dohs/Documents/particularly-hazardous-substances-phs.pdf |
| NIH-DCM | NIH Office of Research Services | application/pdf | ok | 6446 | 7 | https://ors.od.nih.gov/sr/dohs/Documents/working-safely-with-dichloromethane.pdf |
| NIH-DCM-PLAN | NIH Office of Research Services | application/pdf | ok | 27890 | 18 | https://ors.od.nih.gov/sr/dohs/Documents/nih-dichloromethane-health-and-safety-plan.pdf |
| NIH-OEL | NIH Office of Research Services | application/pdf | ok | 2162 | 4 | https://ors.od.nih.gov/sr/dohs/Documents/occupational-exposure-limits-for-chemicals.pdf |
| NIH-FUME-HOOD-CLEAN | NIH Office of Research Services | application/pdf | ok | 5300 | 8 | https://ors.od.nih.gov/sr/dohs/Documents/how-to-safely-clean-cfh-web.pdf |
| NIH-LAB-SOP-TEMPLATE | NIH Office of Research Services | application/pdf | ok | 14854 | 13 | https://ors.od.nih.gov/sr/dohs/Documents/lab-specific-sop-template.pdf |
| NIH-TOXIN | NIH Office of Research Services | application/pdf | ok | 5622 | 7 | https://ors.od.nih.gov/sr/dohs/Documents/exempt-toxin-program-requirements.pdf |
| NIH-INACTIVATION | NIH Office of Research Services | application/pdf | ok | 8102 | 7 | https://ors.od.nih.gov/sr/dohs/Documents/inactivation-method-review-process.pdf |
| CDC-BMBL6 | CDC/NIH | application/pdf | ok | 1504692 | 170 | https://www.cdc.gov/labs/pdf/SF__19_308133-A_BMBL6_00-BOOK-WEB-final-3.pdf |
| NIH-BMBL6 | NIH Office of Research Services | application/pdf | ok | 1504280 | 80 | https://ors.od.nih.gov/sr/dohs/Documents/biosafety-in-microbiological-and-biomedical-laboratories.PDF |
| NIH-LASER | NIH Office of Research Services | application/pdf | ok | 31879 | 25 | https://ors.od.nih.gov/sr/dohs/Documents/laser-safety-program.pdf |
| NIH-LABCOAT | NIH Office of Research Services | application/pdf | ok | 18774 | 12 | https://ors.od.nih.gov/sr/dohs/Documents/laboratory-coat-selection-guidance.pdf |
| NIH-ECP | NIH Office of Research Services | application/pdf | ok | 52134 | 50 | https://ors.od.nih.gov/sr/dohs/Documents/exposure-control-plan.pdf |
| NCBI-PRUDENT-OVERVIEW | National Academies Press / NCBI Bookshelf | text/html | ok | 75193 | 43 | https://www.ncbi.nlm.nih.gov/books/NBK55873/ |
| NCBI-PRUDENT-GENERAL | National Academies Press / NCBI Bookshelf | text/html | ok | 12402 | 8 | https://www.ncbi.nlm.nih.gov/books/NBK55878/ |
| NCBI-PRUDENT-EQUIPMENT | National Academies Press / NCBI Bookshelf | text/html | ok | 31396 | 16 | https://www.ncbi.nlm.nih.gov/books/NBK55882/ |
| NCBI-PRUDENT-CHEMICAL | National Academies Press / NCBI Bookshelf | text/html | ok | 157343 | 67 | https://www.ncbi.nlm.nih.gov/books/NBK55884/ |
| CORNELL-LSM | Cornell University EHS | text/html | ok | 6086 | 3 | https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual |
| CORNELL-CHP | Cornell University EHS | text/html | ok | 17649 | 13 | https://ehs.cornell.edu/research-safety/chemical-safety/chemical-hygiene-plan |
| CORNELL-BIOSAFETY-DOCS | Cornell University EHS | text/html | ok | 2701 | 3 | https://ehs.cornell.edu/research-safety/biosafety-biosecurity/biological-safety-manuals-and-other-documents |
| CORNELL-TRAINING-MATRIX | Cornell University EHS | text/html | ok | 4487 | 8 | https://ehs.cornell.edu/research-safety/general-laboratory-safety/laboratory-safety-training-matrix |
| CORNELL-LASER-PAGE | Cornell University EHS | text/html | ok | 2547 | 2 | https://ehs.cornell.edu/research-safety/radiation-safety/laser-safety |
| CORNELL-SDS | Cornell University EHS | text/html | ok | 1639 | 3 | https://ehs.cornell.edu/research-safety/chemical-safety/safety-data-sheets-chemwatch |
| CORNELL-HW-MANUAL | Cornell University EHS | text/html | ok | 92739 | 79 | https://ehs.cornell.edu/book/export/html/1261 |
| YALE-CHP | Yale Environmental Health & Safety | application/pdf | ok | 192611 | 80 | https://ehs.yale.edu/sites/default/files/files/laboratory-chemical-hygiene-plan.pdf |
| YALE-LASER-SOP | Yale Environmental Health & Safety | application/pdf | ok | 5784 | 4 | https://ehs.yale.edu/sites/default/files/files/laser-sop.pdf |
| YALE-HF | Yale Environmental Health & Safety | application/pdf | ok | 1446 | 0 | https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf |
| YALE-LAB-RULES | Yale Environmental Health & Safety | application/pdf | ok | 1690 | 0 | https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf |
| YALE-MIN-PPE | Yale Environmental Health & Safety | application/pdf | ok | 448 | 0 | https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf |
| YALE-BSC-POSTER | Yale Environmental Health & Safety | application/pdf | ok | 4444 | 1 | https://ehs.yale.edu/sites/default/files/files/biosafety-cabinet-poster.pdf |
| YALE-NEEDLEBOX | Yale Environmental Health & Safety | application/pdf | ok | 364 | 0 | https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf |
| YALE-WASTE-PLACE | Yale Environmental Health & Safety | application/pdf | ok | 2168 | 2 | https://ehs.yale.edu/sites/default/files/files/waste-in-place.pdf |
| YALE-FUME-HOOD-NOTICE | Yale Environmental Health & Safety | application/pdf | ok | 3013 | 3 | https://ehs.yale.edu/sites/default/files/files/fume-hood-repair-notice.pdf |
| YALE-UNATTENDED | Yale Environmental Health & Safety | application/pdf | ok | 845 | 0 | https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf |
| YALE-CHEM-APPROVAL | Yale Environmental Health & Safety | application/pdf | ok | 12140 | 8 | https://ehs.yale.edu/sites/default/files/files/chemicals-ehs-approval.pdf |
| YALE-GENE-DRIVE | Yale Environmental Health & Safety | application/pdf | ok | 18213 | 8 | https://ehs.yale.edu/sites/default/files/files/gene-drive-modified-organisms.pdf |
| YALE-PPE-LABS | Yale Environmental Health & Safety | application/pdf | ok | 11479 | 10 | https://ehs.yale.edu/sites/default/files/files/ppe-procedure-labs.pdf |
| YALE-SHOP-GUIDE | Yale Environmental Health & Safety | text/html | ok | 23746 | 7 | https://ehs.yale.edu/shop-tool-safety |
| YALE-STUDENT-SHOP | Yale Environmental Health & Safety | application/pdf | ok | 1925 | 3 | https://ehs.yale.edu/sites/default/files/files/student-shop-rules.pdf |
| YALE-ART-SAFETY | Yale Environmental Health & Safety | text/html | ok | 23738 | 9 | https://ehs.yale.edu/art-safety |
| BERKELEY-CHP | UC Berkeley Office of Environment, Health & Safety | text/html | ok | 8001 | 7 | https://ehs.berkeley.edu/safety-subjects/chemical-safety/chemical-hygiene-plan |
| BERKELEY-LSM | UC Berkeley Office of Environment, Health & Safety | text/html | ok | 7591 | 7 | https://ehs.berkeley.edu/laboratory-safety-manual |
| BERKELEY-BIOSAFETY | UC Berkeley Office of Environment, Health & Safety | text/html | ok | 384 | 1 | https://ehs.berkeley.edu/publications/biological-safety-program-manual |
| BERKELEY-LASER | UC Berkeley Office of Environment, Health & Safety | text/html | ok | 2767 | 1 | https://ehs.berkeley.edu/laser-safety-manual |
| MIT-CHEMICAL | MIT Environment, Health & Safety | text/html; charset=utf-8 | ok | 2993 | 3 | https://ehs.mit.edu/chemical-safety/ |
| MIT-CHEM-HYGIENE | MIT Environment, Health & Safety | text/html; charset=utf-8 | ok | 8176 | 6 | https://ehs.mit.edu/chemical-safety-program/chemical-hygiene/ |
| STANFORD-CHEM-TOOLKIT | Stanford Environmental Health & Safety | text/html; charset=utf-8 | ok | 3777 | 1 | https://ehs.stanford.edu/forms-tools/laboratory-chemical-safety-toolkit |
| STANFORD-CHEM-WASTE | Stanford Environmental Health & Safety | text/html; charset=utf-8 | ok | 5591 | 4 | https://ehs.stanford.edu/topic/chemical-safety/chemical-waste-disposal |
| STANFORD-BIO-WASTE | Stanford Environmental Health & Safety | text/html; charset=utf-8 | ok | 8794 | 5 | https://ehs.stanford.edu/manual/biosafety-manual/waste |
| STANFORD-FUME-HOOD | Stanford Environmental Health & Safety | text/html; charset=utf-8 | ok | 3293 | 1 | https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/fume-hood-location |
| PRINCETON-CHEM-WASTE | Princeton Environmental Health and Safety | text/html; charset=utf-8 | ok | 13584 | 1 | https://ehs.princeton.edu/laboratory-research/chemical-waste-management |
| UW-CHEM-SAFETY | University of Washington Environmental Health & Safety | text/html; charset=utf-8 | ok | 4607 | 5 | https://www.ehs.washington.edu/chemical/chemical-safety |
| UW-CHEM-WASTE | University of Washington Environmental Health & Safety | text/html; charset=utf-8 | ok | 14438 | 13 | https://www.ehs.washington.edu/chemical/chemical-waste |
| UW-BIO-WASTE | University of Washington Environmental Health & Safety | text/html; charset=utf-8 | ok | 8624 | 9 | https://www.ehs.washington.edu/biological/biohazardous-waste |
| UW-FUME-HOODS | University of Washington Environmental Health & Safety | text/html; charset=utf-8 | ok | 7697 | 8 | https://www.ehs.washington.edu/research-lab/fume-hoods-use-inspection-and-maintenance |
| UCSD-FUME-HOODS | UC San Diego Blink | text/html; charset=utf-8 | ok | 5617 | 6 | https://blink.ucsd.edu/safety/research-lab/chemical/hoods/ |
| UCSD-EXTREME-WASTE | UC San Diego Blink | text/html; charset=utf-8 | ok | 20930 | 14 | https://blink.ucsd.edu/safety/research-lab/hazardous-waste/disposal-guidance/extremely.html |
| UTEXAS-FUME-HOODS | UT Austin Environmental Health & Safety | text/html; charset=utf-8 | ok | 9175 | 7 | https://ehs.utexas.edu/working-safely/equipment-safety/fume-hoods |
| UTEXAS-CHEM-WASTE | UT Austin Environmental Health & Safety | text/html; charset=utf-8 | ok | 24884 | 23 | https://ehs.utexas.edu/environment-waste/waste-management/chemical-waste |
| NCSU-FUME-HOODS | NC State Environmental Health and Safety | text/html; charset=utf-8 | ok | 2163 | 1 | https://ehs.ncsu.edu/laboratory/fume-hoods/ |
| NCSU-LAB-SECURITY | NC State Environmental Health and Safety | text/html; charset=utf-8 | ok | 3547 | 3 | https://ehs.ncsu.edu/laboratory-safety/laboratory-security-and-safety-guidelines/ |
| NCSU-CHEM-HAZARDS | NC State Environmental Health and Safety | text/html; charset=utf-8 | ok | 2786 | 1 | https://ehs.ncsu.edu/laboratory-safety/secondary-safety-contact/chemical-hazards-ssc/ |
| NCSU-CHEM-WASTE | NC State Environmental Health and Safety | text/html; charset=utf-8 | ok | 8652 | 7 | https://ehs.ncsu.edu/home-page-info/environmental-affairs/chemical-waste/ |

## 后续建议

1. 先导入为单独 Dify Dataset：`实验室安全知识库-外部权威来源扩展版`，不要覆盖原 398 条主知识库。
2. 对 `status=external_draft` 的条目进行人工 EHS 审核，审核通过后再合并到正式知识库。
3. 若申报书坚持 3000+ 规模，应继续按本脚本方式扩大来源，而不是拆分旧数据凑数。