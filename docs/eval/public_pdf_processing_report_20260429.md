# 外部 PDF 来源处理报告

- generated_at: `2026-04-29T04:48:32.683053+00:00`
- pdf_source_count: `36`
- pdf_generated_rows: `758`
- bucket_counts: `{'text_ingested': 30, 'short_notice_pdf': 3, 'image_or_poster_pdf': 2, 'short_text_ingested': 1}`
- zero_pdf_count: `5`

## 处理原则

1. 正文型 PDF：用 `pdfminer.six` 自动抽取文本，按章节/语义段生成知识条目，并保留原始 PDF 与抽取文本。
2. 短通知/海报型 PDF：链接和原件保留为证据，但如果抽取文本不足，不硬凑为知识条目。
3. 图片/扫描型 PDF：后续可走 OCR 或人工摘要；OCR/人工处理前，不计入有效知识条目贡献。
4. 所有 PDF 条目都保留 `source_url/source_title/source_org`，便于 Dify 引用追溯和人工审核。

## 分类统计

| 分类 | 数量 | 含义 |
|---|---:|---|
| text_ingested | 30 | 已抽取正文并生成条目 |
| short_text_ingested | 1 | 文本较短但已生成少量条目 |
| image_or_poster_pdf | 2 | 疑似海报/图片型 PDF，需 OCR 或人工摘要 |
| short_notice_pdf | 3 | 短通知 PDF，不自动计入有效条目 |
| needs_review | 0 | 已抽取文本但分段未形成条目，需复核 |

## 需要 OCR / 人工摘要的 PDF

| id | text_chars | raw_bytes | url | 建议 |
|---|---:|---:|---|---|
| YALE-HF | 1446 | 204513 | https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf | PDF 可访问但正文不足，适合作为附属证据或人工摘要，不自动计入有效条目。 |
| YALE-LAB-RULES | 1690 | 188729 | https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf | PDF 可访问但正文不足，适合作为附属证据或人工摘要，不自动计入有效条目。 |
| YALE-MIN-PPE | 448 | 1429600 | https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf | PDF 可访问但文本很少，疑似海报/图片型 PDF；建议 OCR 或人工摘要，不计入有效条目贡献。 |
| YALE-NEEDLEBOX | 364 | 104545 | https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf | PDF 可访问但文本很少，疑似海报/图片型 PDF；建议 OCR 或人工摘要，不计入有效条目贡献。 |
| YALE-UNATTENDED | 845 | 54376 | https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf | PDF 可访问但正文不足，适合作为附属证据或人工摘要，不自动计入有效条目。 |

## 全量 PDF 明细

| id | bucket | rows | text_chars | raw_bytes | url |
|---|---|---:|---:|---:|---|
| YALE-MIN-PPE | image_or_poster_pdf | 0 | 448 | 1429600 | https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf |
| YALE-NEEDLEBOX | image_or_poster_pdf | 0 | 364 | 104545 | https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf |
| YALE-HF | short_notice_pdf | 0 | 1446 | 204513 | https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf |
| YALE-LAB-RULES | short_notice_pdf | 0 | 1690 | 188729 | https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf |
| YALE-UNATTENDED | short_notice_pdf | 0 | 845 | 54376 | https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf |
| YALE-STUDENT-SHOP | short_text_ingested | 3 | 1925 | 144276 | https://ehs.yale.edu/sites/default/files/files/student-shop-rules.pdf |
| CDC-BMBL6 | text_ingested | 170 | 1504692 | 4953083 | https://www.cdc.gov/labs/pdf/SF__19_308133-A_BMBL6_00-BOOK-WEB-final-3.pdf |
| NIH-BMBL6 | text_ingested | 80 | 1504280 | 4559461 | https://ors.od.nih.gov/sr/dohs/Documents/biosafety-in-microbiological-and-biomedical-laboratories.PDF |
| NIH-CABINET | text_ingested | 6 | 5052 | 253225 | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-chemical-storage-cabinets.pdf |
| NIH-CHP | text_ingested | 80 | 182641 | 1750513 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-hygiene-plan.pdf |
| NIH-COMPAT-STORAGE | text_ingested | 3 | 3714 | 265345 | https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-compatible-chemical-storage.pdf |
| NIH-CRYOGEN-FS | text_ingested | 5 | 3691 | 6356026 | https://ors.od.nih.gov/sr/dohs/Documents/cryogen-fact-sheet.pdf |
| NIH-CSG | text_ingested | 66 | 63887 | 38877910 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-safety-guide.pdf |
| NIH-DCM | text_ingested | 7 | 6446 | 208763 | https://ors.od.nih.gov/sr/dohs/Documents/working-safely-with-dichloromethane.pdf |
| NIH-DCM-PLAN | text_ingested | 18 | 27890 | 356312 | https://ors.od.nih.gov/sr/dohs/Documents/nih-dichloromethane-health-and-safety-plan.pdf |
| NIH-ECP | text_ingested | 50 | 52134 | 416109 | https://ors.od.nih.gov/sr/dohs/Documents/exposure-control-plan.pdf |
| NIH-FUME-HOOD-CLEAN | text_ingested | 8 | 5300 | 145046 | https://ors.od.nih.gov/sr/dohs/Documents/how-to-safely-clean-cfh-web.pdf |
| NIH-GAS-CRYO | text_ingested | 24 | 43307 | 776401 | https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf |
| NIH-INACTIVATION | text_ingested | 7 | 8102 | 289223 | https://ors.od.nih.gov/sr/dohs/Documents/inactivation-method-review-process.pdf |
| NIH-LAB-SOP-TEMPLATE | text_ingested | 13 | 14854 | 363989 | https://ors.od.nih.gov/sr/dohs/Documents/lab-specific-sop-template.pdf |
| NIH-LABCOAT | text_ingested | 12 | 18774 | 162799 | https://ors.od.nih.gov/sr/dohs/Documents/laboratory-coat-selection-guidance.pdf |
| NIH-LASER | text_ingested | 25 | 31879 | 965515 | https://ors.od.nih.gov/sr/dohs/Documents/laser-safety-program.pdf |
| NIH-OEL | text_ingested | 4 | 2162 | 37177 | https://ors.od.nih.gov/sr/dohs/Documents/occupational-exposure-limits-for-chemicals.pdf |
| NIH-PEROXIDE | text_ingested | 10 | 6312 | 250972 | https://ors.od.nih.gov/sr/dohs/Documents/managing-peroxide-formers-in-the-lab.pdf |
| NIH-PHS | text_ingested | 9 | 7731 | 322474 | https://ors.od.nih.gov/sr/dohs/Documents/particularly-hazardous-substances-phs.pdf |
| NIH-PYRO | text_ingested | 18 | 22659 | 354828 | https://ors.od.nih.gov/sr/dohs/Documents/managing-pyrophoric-and-water-reactive-chemicals-in-the-laboratories.pdf |
| NIH-SEG | text_ingested | 17 | 12463 | 681833 | https://ors.od.nih.gov/sr/dohs/Documents/chemical-segregation-and-storage.pdf |
| NIH-TOXIN | text_ingested | 7 | 5622 | 162509 | https://ors.od.nih.gov/sr/dohs/Documents/exempt-toxin-program-requirements.pdf |
| YALE-BSC-POSTER | text_ingested | 1 | 4444 | 2696804 | https://ehs.yale.edu/sites/default/files/files/biosafety-cabinet-poster.pdf |
| YALE-CHEM-APPROVAL | text_ingested | 8 | 12140 | 214637 | https://ehs.yale.edu/sites/default/files/files/chemicals-ehs-approval.pdf |
| YALE-CHP | text_ingested | 80 | 192611 | 1175846 | https://ehs.yale.edu/sites/default/files/files/laboratory-chemical-hygiene-plan.pdf |
| YALE-FUME-HOOD-NOTICE | text_ingested | 3 | 3013 | 28026 | https://ehs.yale.edu/sites/default/files/files/fume-hood-repair-notice.pdf |
| YALE-GENE-DRIVE | text_ingested | 8 | 18213 | 113148 | https://ehs.yale.edu/sites/default/files/files/gene-drive-modified-organisms.pdf |
| YALE-LASER-SOP | text_ingested | 4 | 5784 | 144569 | https://ehs.yale.edu/sites/default/files/files/laser-sop.pdf |
| YALE-PPE-LABS | text_ingested | 10 | 11479 | 396978 | https://ehs.yale.edu/sites/default/files/files/ppe-procedure-labs.pdf |
| YALE-WASTE-PLACE | text_ingested | 2 | 2168 | 856073 | https://ehs.yale.edu/sites/default/files/files/waste-in-place.pdf |