#!/usr/bin/env python3
"""Build an external public-source laboratory safety KB import bundle.

This script intentionally collects *new public authoritative sources* instead
of splitting existing local rows. It saves raw HTML/PDF artifacts, extracts
section-level text, converts each section into one structured KB row, and
writes a Dify-ready CSV plus a compact evidence report.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import textwrap
from html.parser import HTMLParser
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

import requests
import warnings

try:
    from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning
except ImportError:  # pragma: no cover - current lightweight env may not include bs4
    BeautifulSoup = None  # type: ignore[assignment]
    XMLParsedAsHTMLWarning = Warning  # type: ignore[assignment]

try:
    from pdfminer.high_level import extract_text
except ImportError:  # pragma: no cover - PDF extraction can use cached text or be skipped
    extract_text = None  # type: ignore[assignment]

REPO_ROOT = Path(__file__).resolve().parents[1]

FIELDS = [
    "id",
    "title",
    "category",
    "subcategory",
    "lab_type",
    "risk_level",
    "hazard_types",
    "scenario",
    "question",
    "answer",
    "steps",
    "ppe",
    "forbidden",
    "disposal",
    "first_aid",
    "emergency",
    "legal_notes",
    "references",
    "source_type",
    "source_title",
    "source_org",
    "source_version",
    "source_date",
    "source_url",
    "last_updated",
    "reviewer",
    "status",
    "tags",
    "language",
]

USER_AGENT = "lab-safe-assistant-public-ingest/1.0 (+local project research)"
warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


@dataclass(frozen=True)
class Source:
    id: str
    title: str
    org: str
    url: str
    category: str
    subcategory: str
    lab_type: str
    hazard_types: str
    source_type: str = "public_authoritative_source"
    version: str = ""
    date: str = ""
    max_sections: int = 35


SOURCES: list[Source] = [
    Source(
        id="OSHA-1910-1450",
        title="OSHA 29 CFR 1910.1450 Occupational Exposure to Hazardous Chemicals in Laboratories",
        org="OSHA",
        url="https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450",
        category="化学",
        subcategory="实验室化学品职业暴露",
        lab_type="化学",
        hazard_types="危险化学品;职业暴露;化学卫生计划",
        version="e-CFR",
        max_sections=45,
    ),
    Source(
        id="NIH-CSG",
        title="NIH Chemical Safety Guide",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/chemical-safety-guide.pdf",
        category="化学",
        subcategory="化学安全指南",
        lab_type="化学",
        hazard_types="危险化学品;PPE;通风柜;储存;废弃物",
        max_sections=100,
    ),
    Source(
        id="NIH-CHP",
        title="NIH Chemical Hygiene Plan",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/chemical-hygiene-plan.pdf",
        category="化学",
        subcategory="化学卫生计划",
        lab_type="化学",
        hazard_types="化学卫生计划;危险化学品;责任分工;SOP",
        max_sections=80,
    ),
    Source(
        id="NIH-SEG",
        title="NIH Chemical Segregation and Storage",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/chemical-segregation-and-storage.pdf",
        category="化学",
        subcategory="化学品分类储存",
        lab_type="化学",
        hazard_types="化学品储存;不相容化学品;腐蚀性;氧化剂;易燃品",
        max_sections=20,
    ),
    Source(
        id="NIH-GAS-CRYO",
        title="NIH Compressed Gas and Cryogen Safety Guidelines",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf",
        category="化学",
        subcategory="压缩气体与低温液体",
        lab_type="化学/物理",
        hazard_types="压缩气体;低温液体;窒息;爆炸;冻伤",
        max_sections=24,
    ),
    Source(
        id="NIH-PEROXIDE",
        title="NIH Managing Peroxide Formers in the Lab",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/managing-peroxide-formers-in-the-lab.pdf",
        category="化学",
        subcategory="过氧化物形成化学品",
        lab_type="化学",
        hazard_types="过氧化物;爆炸;储存期限;检测",
        max_sections=16,
    ),
    Source(
        id="NIH-PYRO",
        title="NIH Managing Pyrophoric and Water Reactive Chemicals in the Laboratories",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/managing-pyrophoric-and-water-reactive-chemicals-in-the-laboratories.pdf",
        category="化学",
        subcategory="自燃和遇水反应化学品",
        lab_type="化学",
        hazard_types="自燃化学品;遇水反应;火灾;惰性气氛",
        max_sections=18,
    ),
    Source(
        id="NIH-COMPAT-STORAGE",
        title="NIH Fact Sheet on Compatible Chemical Storage",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-compatible-chemical-storage.pdf",
        category="化学",
        subcategory="相容化学品储存",
        lab_type="化学",
        hazard_types="化学品储存;不相容化学品;隔离;标签",
        max_sections=14,
    ),
    Source(
        id="NIH-CABINET",
        title="NIH Fact Sheet on Chemical Storage Cabinets",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/fact-sheet-on-chemical-storage-cabinets.pdf",
        category="化学",
        subcategory="化学品储存柜",
        lab_type="化学",
        hazard_types="化学品储存柜;易燃品;腐蚀品;隔离",
        max_sections=12,
    ),
    Source(
        id="NIH-CRYOGEN-FS",
        title="NIH Fact Sheet on Cryogens",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/cryogen-fact-sheet.pdf",
        category="化学",
        subcategory="低温液体",
        lab_type="化学/物理",
        hazard_types="低温液体;冻伤;窒息;压力风险",
        max_sections=20,
    ),
    Source(
        id="NIH-PHS",
        title="NIH Fact Sheet on Particularly Hazardous Substances",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/particularly-hazardous-substances-phs.pdf",
        category="化学",
        subcategory="特别危险物质",
        lab_type="化学",
        hazard_types="致癌物;急性毒性;生殖毒性;指定区域",
        max_sections=16,
    ),
    Source(
        id="NIH-DCM",
        title="NIH Working Safely with Dichloromethane",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/working-safely-with-dichloromethane.pdf",
        category="化学",
        subcategory="二氯甲烷安全",
        lab_type="化学",
        hazard_types="二氯甲烷;挥发性溶剂;职业暴露;通风柜",
        max_sections=14,
    ),
    Source(
        id="NIH-DCM-PLAN",
        title="NIH Dichloromethane Health and Safety Plan",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/nih-dichloromethane-health-and-safety-plan.pdf",
        category="化学",
        subcategory="二氯甲烷健康安全计划",
        lab_type="化学",
        hazard_types="二氯甲烷;健康安全计划;暴露控制;监测",
        max_sections=18,
    ),
    Source(
        id="NIH-OEL",
        title="NIH Occupational Exposure Limits for Chemicals",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/occupational-exposure-limits-for-chemicals.pdf",
        category="化学",
        subcategory="职业暴露限值",
        lab_type="化学",
        hazard_types="职业暴露限值;化学品;监测;风险评估",
        max_sections=10,
    ),
    Source(
        id="NIH-FUME-HOOD-CLEAN",
        title="NIH How to Safely Clean Chemical Fume Hoods",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/how-to-safely-clean-cfh-web.pdf",
        category="化学",
        subcategory="通风柜清洁",
        lab_type="化学",
        hazard_types="通风柜;污染清洁;PPE;化学残留",
        max_sections=12,
    ),
    Source(
        id="NIH-LAB-SOP-TEMPLATE",
        title="NIH Lab Specific SOP Template",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/lab-specific-sop-template.pdf",
        category="通用",
        subcategory="实验室专用 SOP 模板",
        lab_type="通用",
        hazard_types="SOP;风险评估;PPE;操作控制",
        max_sections=18,
    ),
    Source(
        id="NIH-TOXIN",
        title="NIH Exempt Toxin Program Requirements",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/exempt-toxin-program-requirements.pdf",
        category="生物",
        subcategory="毒素项目要求",
        lab_type="生物/化学",
        hazard_types="生物毒素;库存;安保;审批",
        max_sections=12,
    ),
    Source(
        id="NIH-INACTIVATION",
        title="NIH SOP 900 Approval Process for Inactivation Methods for Infectious Material",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/inactivation-method-review-process.pdf",
        category="生物",
        subcategory="感染性材料灭活审批",
        lab_type="生物",
        hazard_types="感染性材料;灭活;审批;验证",
        max_sections=14,
    ),
    Source(
        id="CDC-BMBL6",
        title="Biosafety in Microbiological and Biomedical Laboratories (BMBL), 6th Edition",
        org="CDC/NIH",
        url="https://www.cdc.gov/labs/pdf/SF__19_308133-A_BMBL6_00-BOOK-WEB-final-3.pdf",
        category="生物",
        subcategory="生物安全",
        lab_type="生物",
        hazard_types="生物安全;BSL;病原微生物;暴露控制",
        version="6th Edition",
        max_sections=170,
    ),
    Source(
        id="NIH-BMBL6",
        title="NIH-hosted BMBL 6th Edition",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/biosafety-in-microbiological-and-biomedical-laboratories.PDF",
        category="生物",
        subcategory="生物安全",
        lab_type="生物",
        hazard_types="生物安全;BSL;病原微生物;暴露控制",
        version="6th Edition",
        max_sections=80,
    ),
    Source(
        id="NIH-LASER",
        title="NIH Laser Safety Program",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/laser-safety-program.pdf",
        category="物理",
        subcategory="激光安全",
        lab_type="物理/工程",
        hazard_types="激光;眼损伤;皮肤损伤;受控区域",
        max_sections=25,
    ),
    Source(
        id="NIH-LABCOAT",
        title="NIH Guidance for the Selection of Laboratory Coats",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/laboratory-coat-selection-guidance.pdf",
        category="通用",
        subcategory="PPE",
        lab_type="通用",
        hazard_types="PPE;实验服;化学飞溅;火焰风险",
        max_sections=12,
    ),
    Source(
        id="NIH-ECP",
        title="NIH Exposure Control Program",
        org="NIH Office of Research Services",
        url="https://ors.od.nih.gov/sr/dohs/Documents/exposure-control-plan.pdf",
        category="生物",
        subcategory="血源性病原体暴露控制",
        lab_type="生物/医学",
        hazard_types="血源性病原体;暴露控制;锐器;PPE",
        max_sections=50,
    ),
    Source(
        id="NCBI-PRUDENT-OVERVIEW",
        title="Prudent Practices in the Laboratory: Handling and Management of Chemical Hazards",
        org="National Academies Press / NCBI Bookshelf",
        url="https://www.ncbi.nlm.nih.gov/books/NBK55873/",
        category="化学",
        subcategory="化学品审慎实践",
        lab_type="化学",
        hazard_types="危险化学品;风险评估;管理体系;通风;废弃物",
        max_sections=70,
    ),
    Source(
        id="NCBI-PRUDENT-GENERAL",
        title="Prudent Practices in the Laboratory - General Laboratory Safety",
        org="National Academies Press / NCBI Bookshelf",
        url="https://www.ncbi.nlm.nih.gov/books/NBK55878/",
        category="通用",
        subcategory="通用实验室安全",
        lab_type="通用",
        hazard_types="通用安全;PPE;培训;设施",
        max_sections=28,
    ),
    Source(
        id="NCBI-PRUDENT-EQUIPMENT",
        title="Prudent Practices in the Laboratory - Laboratory Equipment",
        org="National Academies Press / NCBI Bookshelf",
        url="https://www.ncbi.nlm.nih.gov/books/NBK55882/",
        category="通用",
        subcategory="实验室设备安全",
        lab_type="通用",
        hazard_types="设备安全;通风柜;玻璃器皿;压力系统",
        max_sections=28,
    ),
    Source(
        id="NCBI-PRUDENT-CHEMICAL",
        title="Prudent Practices in the Laboratory - Working with Chemicals",
        org="National Academies Press / NCBI Bookshelf",
        url="https://www.ncbi.nlm.nih.gov/books/NBK55884/",
        category="化学",
        subcategory="化学品操作",
        lab_type="化学",
        hazard_types="危险化学品;操作控制;储存;废弃物;应急",
        max_sections=100,
    ),
    Source(
        id="CORNELL-LSM",
        title="Cornell Laboratory Safety Manual",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual",
        category="通用",
        subcategory="实验室安全手册",
        lab_type="通用",
        hazard_types="实验室安全;责任分工;PPE;培训;应急",
        max_sections=35,
    ),
    Source(
        id="CORNELL-CHP",
        title="Cornell Chemical Hygiene Plan",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/chemical-safety/chemical-hygiene-plan",
        category="化学",
        subcategory="化学卫生计划",
        lab_type="化学",
        hazard_types="化学卫生计划;SOP;危险化学品;培训",
        max_sections=30,
    ),
    Source(
        id="CORNELL-BIOSAFETY-DOCS",
        title="Cornell Biological Safety Manuals and Other Documents",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/biosafety-biosecurity/biological-safety-manuals-and-other-documents",
        category="生物",
        subcategory="生物安全文件",
        lab_type="生物",
        hazard_types="生物安全;BSL;暴露控制;生物废物",
        max_sections=20,
    ),
    Source(
        id="CORNELL-TRAINING-MATRIX",
        title="Cornell Laboratory Safety Training Matrix",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/general-laboratory-safety/laboratory-safety-training-matrix",
        category="培训",
        subcategory="实验室安全培训矩阵",
        lab_type="通用",
        hazard_types="培训;准入;化学;生物;辐射;激光",
        max_sections=20,
    ),
    Source(
        id="CORNELL-LASER-PAGE",
        title="Cornell Laser Safety",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/radiation-safety/laser-safety",
        category="物理",
        subcategory="激光安全",
        lab_type="物理/工程",
        hazard_types="激光;注册;培训;PPE",
        max_sections=16,
    ),
    Source(
        id="CORNELL-SDS",
        title="Cornell Safety Data Sheets Chemwatch",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/research-safety/chemical-safety/safety-data-sheets-chemwatch",
        category="化学",
        subcategory="安全数据表 SDS",
        lab_type="化学",
        hazard_types="SDS;化学品信息;危害沟通",
        max_sections=10,
    ),
    Source(
        id="CORNELL-HW-MANUAL",
        title="Cornell Hazardous Waste Manual",
        org="Cornell University EHS",
        url="https://ehs.cornell.edu/book/export/html/1261",
        category="废弃物",
        subcategory="危险废物手册",
        lab_type="通用",
        hazard_types="危险废物;标签;暂存;处置;卫星积累区",
        max_sections=150,
    ),
    Source(
        id="YALE-CHP",
        title="Yale Laboratory Chemical Hygiene Plan",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/laboratory-chemical-hygiene-plan.pdf",
        category="化学",
        subcategory="化学卫生计划",
        lab_type="化学",
        hazard_types="化学卫生计划;PPE;通风柜;高危化学品",
        max_sections=80,
    ),
    Source(
        id="YALE-LASER-SOP",
        title="Yale Laser Standard Operating Procedure",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/laser-sop.pdf",
        category="物理",
        subcategory="激光 SOP",
        lab_type="物理/工程",
        hazard_types="激光;SOP;受控区域;眼损伤",
        max_sections=16,
    ),
    Source(
        id="YALE-HF",
        title="Yale Hydrofluoric Acid Emergency Response",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/hydrofluoric-acid-exposure.pdf",
        category="化学",
        subcategory="氢氟酸应急",
        lab_type="化学",
        hazard_types="氢氟酸;腐蚀;急救;应急响应",
        max_sections=12,
    ),
    Source(
        id="YALE-LAB-RULES",
        title="Yale Laboratory Safety Rules",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/lab-safety-rules.pdf",
        category="通用",
        subcategory="实验室安全规则",
        lab_type="通用",
        hazard_types="实验室规则;PPE;禁止事项;通用安全",
        max_sections=8,
    ),
    Source(
        id="YALE-MIN-PPE",
        title="Yale Minimum Lab PPE",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/minimum-lab-ppe.pdf",
        category="通用",
        subcategory="最低实验室 PPE",
        lab_type="通用",
        hazard_types="PPE;护目镜;实验服;手套",
        max_sections=8,
    ),
    Source(
        id="YALE-BSC-POSTER",
        title="Yale Working Safely in Your Biosafety Cabinet",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/biosafety-cabinet-poster.pdf",
        category="生物",
        subcategory="生物安全柜",
        lab_type="生物",
        hazard_types="生物安全柜;气流;污染控制;PPE",
        max_sections=10,
    ),
    Source(
        id="YALE-NEEDLEBOX",
        title="Yale Needlebox Disposal Poster",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/needlebox-disposal.pdf",
        category="生物",
        subcategory="锐器盒处置",
        lab_type="生物/医学",
        hazard_types="锐器;针头;生物废物;刺伤",
        max_sections=6,
    ),
    Source(
        id="YALE-WASTE-PLACE",
        title="Yale Put Waste In Its Place",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/waste-in-place.pdf",
        category="通用",
        subcategory="废弃物分类",
        lab_type="通用",
        hazard_types="废弃物;分类;标签;容器",
        max_sections=8,
    ),
    Source(
        id="YALE-FUME-HOOD-NOTICE",
        title="Yale Fume Hood Repair Notice",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/fume-hood-repair-notice.pdf",
        category="化学",
        subcategory="通风柜维修",
        lab_type="化学",
        hazard_types="通风柜;维修;停用;工程控制",
        max_sections=4,
    ),
    Source(
        id="YALE-UNATTENDED",
        title="Yale Emergency Information for Unattended Operations",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/unattended-operations.pdf",
        category="通用",
        subcategory="无人值守操作",
        lab_type="通用",
        hazard_types="无人值守;应急信息;风险控制",
        max_sections=6,
    ),
    Source(
        id="YALE-CHEM-APPROVAL",
        title="Yale Chemicals Requiring EHS Pre-Approval",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/chemicals-ehs-approval.pdf",
        category="化学",
        subcategory="需 EHS 预审批化学品",
        lab_type="化学",
        hazard_types="预审批;高危化学品;采购;使用控制",
        max_sections=8,
    ),
    Source(
        id="YALE-GENE-DRIVE",
        title="Yale Gene Drive Modified Organisms",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/gene-drive-modified-organisms.pdf",
        category="生物",
        subcategory="基因驱动修饰生物",
        lab_type="生物",
        hazard_types="基因驱动;GMO;生物安全;遏制",
        max_sections=8,
    ),
    Source(
        id="YALE-PPE-LABS",
        title="Yale PPE Procedure for Clinical Laboratories",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/ppe-procedure-labs.pdf",
        category="通用",
        subcategory="临床实验室 PPE 程序",
        lab_type="医学/生物",
        hazard_types="PPE;临床实验室;暴露控制",
        max_sections=12,
    ),
    Source(
        id="YALE-SHOP-GUIDE",
        title="Yale Shop and Tool Safety",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/shop-tool-safety",
        category="设备安全",
        subcategory="车间安全",
        lab_type="工程/物理",
        hazard_types="机械;工具;PPE;车间",
        max_sections=8,
    ),
    Source(
        id="YALE-STUDENT-SHOP",
        title="Yale Student Shop Rules",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/sites/default/files/files/student-shop-rules.pdf",
        category="设备安全",
        subcategory="学生车间规则",
        lab_type="工程/物理",
        hazard_types="机械;学生车间;培训;PPE",
        max_sections=8,
    ),
    Source(
        id="YALE-ART-SAFETY",
        title="Yale Art Safety",
        org="Yale Environmental Health & Safety",
        url="https://ehs.yale.edu/art-safety",
        category="通用",
        subcategory="艺术材料安全",
        lab_type="艺术/设计",
        hazard_types="艺术材料;化学品;通风;PPE",
        max_sections=10,
    ),
    Source(
        id="BERKELEY-CHP",
        title="UC Berkeley Chemical Hygiene Plan",
        org="UC Berkeley Office of Environment, Health & Safety",
        url="https://ehs.berkeley.edu/safety-subjects/chemical-safety/chemical-hygiene-plan",
        category="化学",
        subcategory="化学卫生计划",
        lab_type="化学",
        hazard_types="化学卫生计划;危险化学品;PPE;通风柜",
        max_sections=28,
    ),
    Source(
        id="BERKELEY-LSM",
        title="UC Berkeley Laboratory Safety Manual",
        org="UC Berkeley Office of Environment, Health & Safety",
        url="https://ehs.berkeley.edu/laboratory-safety-manual",
        category="通用",
        subcategory="实验室安全手册",
        lab_type="通用",
        hazard_types="实验室安全;培训;PPE;应急",
        max_sections=28,
    ),
    Source(
        id="BERKELEY-BIOSAFETY",
        title="UC Berkeley Biological Safety Program Manual",
        org="UC Berkeley Office of Environment, Health & Safety",
        url="https://ehs.berkeley.edu/publications/biological-safety-program-manual",
        category="生物",
        subcategory="生物安全手册",
        lab_type="生物",
        hazard_types="生物安全;BSL;暴露控制;废弃物",
        max_sections=30,
    ),
    Source(
        id="BERKELEY-LASER",
        title="UC Berkeley Laser Safety Manual",
        org="UC Berkeley Office of Environment, Health & Safety",
        url="https://ehs.berkeley.edu/laser-safety-manual",
        category="物理",
        subcategory="激光安全手册",
        lab_type="物理/工程",
        hazard_types="激光;受控区域;眼损伤;联锁",
        max_sections=24,
    ),
    Source(
        id="MIT-CHEMICAL",
        title="MIT Chemical Safety",
        org="MIT Environment, Health & Safety",
        url="https://ehs.mit.edu/chemical-safety/",
        category="化学",
        subcategory="化学安全",
        lab_type="化学",
        hazard_types="化学品;SDS;通风柜;储存;废弃物",
        max_sections=18,
    ),
    Source(
        id="MIT-CHEM-HYGIENE",
        title="MIT Chemical Hygiene",
        org="MIT Environment, Health & Safety",
        url="https://ehs.mit.edu/chemical-safety-program/chemical-hygiene/",
        category="化学",
        subcategory="化学卫生",
        lab_type="化学",
        hazard_types="化学卫生计划;危险化学品;PPE;培训",
        max_sections=35,
    ),
    Source(
        id="STANFORD-CHEM-TOOLKIT",
        title="Stanford Laboratory Chemical Safety Toolkit",
        org="Stanford Environmental Health & Safety",
        url="https://ehs.stanford.edu/forms-tools/laboratory-chemical-safety-toolkit",
        category="化学",
        subcategory="实验室化学安全工具包",
        lab_type="化学",
        hazard_types="化学安全;SOP;PPE;风险评估",
        max_sections=16,
    ),
    Source(
        id="STANFORD-CHEM-WASTE",
        title="Stanford Chemical Waste Disposal",
        org="Stanford Environmental Health & Safety",
        url="https://ehs.stanford.edu/topic/chemical-safety/chemical-waste-disposal",
        category="废弃物",
        subcategory="化学废物处置",
        lab_type="化学",
        hazard_types="化学废物;标签;容器;处置",
        max_sections=20,
    ),
    Source(
        id="STANFORD-BIO-WASTE",
        title="Stanford Biosafety Manual - Waste",
        org="Stanford Environmental Health & Safety",
        url="https://ehs.stanford.edu/manual/biosafety-manual/waste",
        category="生物",
        subcategory="生物废物",
        lab_type="生物",
        hazard_types="生物废物;灭菌;锐器;处置",
        max_sections=24,
    ),
    Source(
        id="STANFORD-FUME-HOOD",
        title="Stanford Laboratory Standard Design Guidelines - Fume Hood Location",
        org="Stanford Environmental Health & Safety",
        url="https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/fume-hood-location",
        category="化学",
        subcategory="通风柜位置与设计",
        lab_type="化学",
        hazard_types="通风柜;实验室设计;排风;工程控制",
        max_sections=14,
    ),
    Source(
        id="PRINCETON-CHEM-WASTE",
        title="Princeton Chemical Waste Management",
        org="Princeton Environmental Health and Safety",
        url="https://ehs.princeton.edu/laboratory-research/chemical-waste-management",
        category="废弃物",
        subcategory="化学废物管理",
        lab_type="化学",
        hazard_types="化学废物;标签;容器;暂存;处置",
        max_sections=40,
    ),
    Source(
        id="UW-CHEM-SAFETY",
        title="UW Chemical Safety",
        org="University of Washington Environmental Health & Safety",
        url="https://www.ehs.washington.edu/chemical/chemical-safety",
        category="化学",
        subcategory="化学安全",
        lab_type="化学",
        hazard_types="化学品;SDS;储存;培训",
        max_sections=20,
    ),
    Source(
        id="UW-CHEM-WASTE",
        title="UW Chemical Waste",
        org="University of Washington Environmental Health & Safety",
        url="https://www.ehs.washington.edu/chemical/chemical-waste",
        category="废弃物",
        subcategory="化学废物",
        lab_type="化学",
        hazard_types="化学废物;标签;容器;处置",
        max_sections=35,
    ),
    Source(
        id="UW-BIO-WASTE",
        title="UW Biohazardous Waste",
        org="University of Washington Environmental Health & Safety",
        url="https://www.ehs.washington.edu/biological/biohazardous-waste",
        category="生物",
        subcategory="生物危害废物",
        lab_type="生物",
        hazard_types="生物危害废物;锐器;灭菌;处置",
        max_sections=28,
    ),
    Source(
        id="UW-FUME-HOODS",
        title="UW Fume Hoods Use Inspection and Maintenance",
        org="University of Washington Environmental Health & Safety",
        url="https://www.ehs.washington.edu/research-lab/fume-hoods-use-inspection-and-maintenance",
        category="化学",
        subcategory="通风柜使用检查维护",
        lab_type="化学",
        hazard_types="通风柜;检查;维护;工程控制",
        max_sections=24,
    ),
    Source(
        id="UCSD-FUME-HOODS",
        title="UC San Diego Chemical Fume Hoods Overview",
        org="UC San Diego Blink",
        url="https://blink.ucsd.edu/safety/research-lab/chemical/hoods/",
        category="化学",
        subcategory="通风柜",
        lab_type="化学",
        hazard_types="通风柜;排风;操作规范;工程控制",
        max_sections=24,
    ),
    Source(
        id="UCSD-EXTREME-WASTE",
        title="UC San Diego Extremely Hazardous Chemical Waste",
        org="UC San Diego Blink",
        url="https://blink.ucsd.edu/safety/research-lab/hazardous-waste/disposal-guidance/extremely.html",
        category="废弃物",
        subcategory="极高危化学废物",
        lab_type="化学",
        hazard_types="极高危废物;标签;处置;暂存",
        max_sections=60,
    ),
    Source(
        id="UTEXAS-FUME-HOODS",
        title="UT Austin Fume Hoods",
        org="UT Austin Environmental Health & Safety",
        url="https://ehs.utexas.edu/working-safely/equipment-safety/fume-hoods",
        category="化学",
        subcategory="通风柜",
        lab_type="化学",
        hazard_types="通风柜;检查;操作;工程控制",
        max_sections=24,
    ),
    Source(
        id="UTEXAS-CHEM-WASTE",
        title="UT Austin Chemical Waste",
        org="UT Austin Environmental Health & Safety",
        url="https://ehs.utexas.edu/environment-waste/waste-management/chemical-waste",
        category="废弃物",
        subcategory="化学废物",
        lab_type="化学",
        hazard_types="化学废物;标签;容器;处置",
        max_sections=70,
    ),
    Source(
        id="NCSU-FUME-HOODS",
        title="NC State Fume Hoods and Lab Exhaust",
        org="NC State Environmental Health and Safety",
        url="https://ehs.ncsu.edu/laboratory/fume-hoods/",
        category="化学",
        subcategory="通风柜和实验室排风",
        lab_type="化学",
        hazard_types="通风柜;实验室排风;维护;检查",
        max_sections=14,
    ),
    Source(
        id="NCSU-LAB-SECURITY",
        title="NC State Laboratory Security and Safety Guidelines",
        org="NC State Environmental Health and Safety",
        url="https://ehs.ncsu.edu/laboratory-safety/laboratory-security-and-safety-guidelines/",
        category="通用",
        subcategory="实验室安全与安保指南",
        lab_type="通用",
        hazard_types="实验室安全;安保;准入;通用规则",
        max_sections=16,
    ),
    Source(
        id="NCSU-CHEM-HAZARDS",
        title="NC State Chemical Hazards SSC",
        org="NC State Environmental Health and Safety",
        url="https://ehs.ncsu.edu/laboratory-safety/secondary-safety-contact/chemical-hazards-ssc/",
        category="化学",
        subcategory="化学危害",
        lab_type="化学",
        hazard_types="化学危害;二级安全联系人;风险控制",
        max_sections=16,
    ),
    Source(
        id="NCSU-CHEM-WASTE",
        title="NC State Chemical Waste",
        org="NC State Environmental Health and Safety",
        url="https://ehs.ncsu.edu/home-page-info/environmental-affairs/chemical-waste/",
        category="废弃物",
        subcategory="化学废物",
        lab_type="化学",
        hazard_types="化学废物;标签;容器;处置",
        max_sections=28,
    ),
]


def now_date() -> str:
    return datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d")


def normalize_text(text: str) -> str:
    text = text.replace("\x00", " ")
    text = re.sub(r"[ \t\r\f\v]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def safe_name(source: Source, suffix: str) -> str:
    parsed = urlparse(source.url)
    stem = Path(parsed.path).name or parsed.netloc
    stem = re.sub(r"[^A-Za-z0-9_.-]+", "_", stem)[:80]
    return f"{source.id}_{stem}.{suffix}"


def download(source: Source, raw_dir: Path) -> tuple[bytes, str, Path]:
    raw_dir.mkdir(parents=True, exist_ok=True)
    parsed = urlparse(source.url)
    expected_pdf = source.url.lower().split("?", 1)[0].endswith(".pdf")
    expected_suffix = "pdf" if expected_pdf else "html"
    cached = raw_dir / safe_name(source, expected_suffix)
    if cached.exists() and cached.stat().st_size > 0:
        ctype = "application/pdf" if expected_pdf else "text/html"
        return cached.read_bytes(), ctype, cached
    resp = requests.get(
        source.url,
        timeout=60,
        headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/pdf,*/*"},
    )
    resp.raise_for_status()
    ctype = resp.headers.get("content-type", "").lower()
    is_pdf = "pdf" in ctype or source.url.lower().split("?", 1)[0].endswith(".pdf")
    path = raw_dir / safe_name(source, "pdf" if is_pdf else "html")
    path.write_bytes(resp.content)
    return resp.content, ctype, path


def extract_html_text(blob: bytes) -> str:
    if BeautifulSoup is None:
        return extract_html_text_stdlib(blob)
    soup = BeautifulSoup(blob, "lxml")
    for tag in soup(["script", "style", "noscript", "svg", "form"]):
        tag.decompose()
    main = (
        soup.find("main")
        or soup.find("article")
        or soup.find(class_=re.compile(r"(main|content|body|field|node)", re.I))
        or soup.body
        or soup
    )
    lines = []
    nodes = main.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "div", "span"])
    if not nodes:
        nodes = soup.find_all(["h1", "h2", "h3", "h4", "p", "li", "td", "th", "div", "span"])
    seen_text: set[str] = set()
    for node in nodes:
        text = node.get_text(" ", strip=True)
        text = re.sub(r"\s+", " ", text).strip()
        if not text:
            continue
        if text in seen_text:
            continue
        seen_text.add(text)
        if len(text) < 3:
            continue
        if text.lower() in {"home", "search", "main menu", "skip to main content"}:
            continue
        prefix = "\n## " if node.name in {"h1", "h2", "h3"} else "\n"
        lines.append(prefix + text)
    extracted = normalize_text("\n".join(lines))
    if len(extracted) < 500:
        # Some Drupal/EHS pages put the meaningful text in generic containers
        # that are filtered poorly. Fall back to full-page text, still after
        # removing script/style/navigation chrome.
        fallback = soup.get_text("\n", strip=True)
        fallback_lines = []
        for line in fallback.splitlines():
            line = re.sub(r"\s+", " ", line).strip()
            if len(line) >= 20 and line.lower() not in {"skip to main content", "submit search"}:
                fallback_lines.append(line)
        fallback = normalize_text("\n".join(dict.fromkeys(fallback_lines)))
        if len(fallback) > len(extracted):
            extracted = fallback
    return extracted


def extract_pdf_text(blob: bytes) -> str:
    if extract_text is None:
        raise RuntimeError("pdfminer.six is not installed; use cached extracted text or install pdfminer.six")
    return normalize_text(extract_text(io.BytesIO(blob)) or "")


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []
        self.skip_stack: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "form"}:
            self.skip_stack.append(tag.lower())
        if tag.lower() in {"h1", "h2", "h3", "h4", "p", "li", "td", "th", "div"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.skip_stack and self.skip_stack[-1] == tag.lower():
            self.skip_stack.pop()
        if tag.lower() in {"h1", "h2", "h3", "h4", "p", "li", "td", "th", "div"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self.skip_stack:
            self.parts.append(data)


def extract_html_text_stdlib(blob: bytes) -> str:
    raw = blob.decode("utf-8", errors="ignore")
    parser = _HTMLTextExtractor()
    parser.feed(raw[:1_500_000])
    lines: list[str] = []
    seen: set[str] = set()
    for line in "".join(parser.parts).splitlines():
        line = re.sub(r"\s+", " ", line).strip()
        if len(line) < 20:
            continue
        low = line.lower()
        if low in {"skip to main content", "submit search"}:
            continue
        if line in seen:
            continue
        seen.add(line)
        lines.append(line)
    return normalize_text("\n".join(lines))


def extract_text_for_source(source: Source, blob: bytes, ctype: str, raw_path: Path, text_dir: Path) -> str:
    """Extract text with cache to avoid re-parsing large PDFs on reruns."""
    text_path = text_dir / f"{source.id}.txt"
    if text_path.exists() and text_path.stat().st_size > 0:
        return text_path.read_text(encoding="utf-8", errors="ignore")
    is_pdf = "pdf" in ctype or raw_path.suffix.lower() == ".pdf"
    text = extract_pdf_text(blob) if is_pdf else extract_html_text(blob)
    text_path.write_text(text, encoding="utf-8")
    return text


def split_sections(text: str, source: Source) -> list[tuple[str, str]]:
    lines = [ln.strip() for ln in text.splitlines()]
    sections: list[tuple[str, list[str]]] = []
    current_title = source.title
    current_body: list[str] = []

    heading_re = re.compile(
        r"^(?:#{1,3}\s*)?(?:\d+(?:\.\d+){0,3}\s+)?[A-Z][A-Za-z0-9,;:()/%\-–—'’& ]{4,120}$"
    )
    numbered_re = re.compile(r"^(?:\d+(?:\.\d+){1,4}|[A-Z]\.|\([a-z0-9ivx]+\))\s+.{4,120}$")

    def flush() -> None:
        nonlocal current_body, current_title
        body = normalize_text("\n".join(current_body))
        if len(body) >= 260:
            sections.append((current_title.strip()[:140], body))
        current_body = []

    for raw in lines:
        line = raw.strip("# ").strip()
        if not line:
            continue
        # Avoid repeated website navigation fragments.
        if line in {source.title, source.org} and current_body:
            continue
        is_heading = False
        if raw.startswith("## "):
            is_heading = True
        elif len(line) <= 120 and (heading_re.match(line) or numbered_re.match(line)):
            # A short title-cased/numbered standalone line in PDF output.
            is_heading = True
        if is_heading and len(current_body) >= 3:
            flush()
            current_title = line
        else:
            current_body.append(line)
            # Very long sections are split into manageable Dify documents.
            if sum(len(x) for x in current_body) > 2400:
                flush()
                current_title = f"{line[:80]}（续）" if len(line) > 20 else current_title
    flush()

    # Fallback paragraph chunking when headings are not extracted well.
    if len(sections) < 3:
        paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if len(p.strip()) >= 260]
        sections = [(f"{source.title} - section {i}", p) for i, p in enumerate(paragraphs, 1)]

    # Deduplicate and trim.
    seen: set[str] = set()
    out: list[tuple[str, str]] = []
    for title, body in sections:
        body = normalize_text(body)
        if len(body) < 260:
            continue
        digest = hashlib.sha256(re.sub(r"\W+", "", body.lower()).encode("utf-8")).hexdigest()[:16]
        if digest in seen:
            continue
        seen.add(digest)
        out.append((clean_title(title, source), body[:3200]))
        if len(out) >= source.max_sections:
            break
    return out


def clean_title(title: str, source: Source) -> str:
    title = re.sub(r"\s+", " ", title).strip(" -|")
    noisy = {"skip to main content", "search", "main menu"}
    if not title or title.lower() in noisy or len(title) < 4:
        return source.title
    return title[:140]


def classify_risk(text: str, source: Source) -> str:
    lowered = text.lower()
    high = ["pyrophoric", "hydrofluoric", "explosive", "peroxide", "class 4", "toxic gas", "select carcinogen"]
    med = ["flammable", "corrosive", "compressed gas", "biosafety level 2", "bsl-2", "laser", "cryogen"]
    if any(k in lowered for k in high):
        return "4"
    if any(k in lowered for k in med):
        return "3"
    if source.category in {"化学", "生物", "物理"}:
        return "2"
    return "1"


def extract_steps(text: str) -> str:
    sentences = split_sentences(text)
    picks = [
        s for s in sentences
        if re.search(r"\b(must|shall|should|required|ensure|use|wear|store|keep|label|dispose|report|contact|avoid)\b", s, re.I)
    ][:6]
    if not picks:
        picks = sentences[:4]
    return "; ".join(shorten(s, 120) for s in picks if s)[:900]


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text)
    parts = re.split(r"(?<=[.!?。！？])\s+", text)
    return [p.strip() for p in parts if len(p.strip()) >= 30]


def shorten(text: str, width: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    return textwrap.shorten(text, width=width, placeholder="...")


def make_answer(body: str) -> str:
    sentences = split_sentences(body)
    selected = sentences[:7]
    answer = " ".join(selected)
    if len(answer) < 180:
        answer = body[:900]
    return answer[:1400]


def row_for(source: Source, idx: int, title: str, body: str) -> dict[str, str]:
    digest = hashlib.sha256(f"{source.url}\n{title}\n{body[:500]}".encode("utf-8")).hexdigest()[:10]
    question_title = title if title != source.title else source.subcategory
    return {
        "id": f"EXT-{source.id}-{idx:03d}-{digest}",
        "title": f"{source.title} - {title}"[:180],
        "category": source.category,
        "subcategory": source.subcategory,
        "lab_type": source.lab_type,
        "risk_level": classify_risk(body, source),
        "hazard_types": source.hazard_types,
        "scenario": f"参考{source.org}公开资料处理{source.subcategory}相关实验室安全问题",
        "question": f"{question_title}相关的实验室安全要求是什么？"[:180],
        "answer": make_answer(body),
        "steps": extract_steps(body),
        "ppe": infer_ppe(body),
        "forbidden": infer_forbidden(body),
        "disposal": infer_disposal(body),
        "first_aid": infer_first_aid(body),
        "emergency": infer_emergency(body),
        "legal_notes": "公开权威资料整理，落地执行时需结合本单位SOP、SDS、EHS审批和适用法规。",
        "references": f"{source.org}: {source.title}; section: {title}",
        "source_type": source.source_type,
        "source_title": source.title,
        "source_org": source.org,
        "source_version": source.version,
        "source_date": source.date,
        "source_url": source.url,
        "last_updated": now_date(),
        "reviewer": "auto-ingest; pending human EHS review",
        "status": "external_draft",
        "tags": ";".join(filter(None, ["external_public_source", source.id, source.category, source.subcategory])),
        "language": "en-US/zh-CN-meta",
    }


def infer_ppe(text: str) -> str:
    lowered = text.lower()
    ppe = []
    if any(k in lowered for k in ["eye", "goggle", "face shield", "laser"]):
        ppe.append("护目镜/面屏")
    if any(k in lowered for k in ["glove", "hand"]):
        ppe.append("合适材质手套")
    if any(k in lowered for k in ["lab coat", "coat", "flame"]):
        ppe.append("实验服/阻燃实验服")
    if any(k in lowered for k in ["respirator", "aerosol", "biological"]):
        ppe.append("必要时呼吸防护")
    return ";".join(ppe) or "按SDS、风险评估和本单位SOP选择PPE"


def infer_forbidden(text: str) -> str:
    lowered = text.lower()
    items = []
    if "food" in lowered or "drink" in lowered:
        items.append("禁止在实验区饮食")
    if "incompatible" in lowered:
        items.append("禁止混放不相容化学品")
    if "unattended" in lowered:
        items.append("禁止未经风险控制的无人值守操作")
    if "mouth pipetting" in lowered:
        items.append("禁止口吸移液")
    return ";".join(items) or "禁止绕过工程控制、PPE、培训和审批要求"


def infer_disposal(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["waste", "dispose", "disposal"]):
        return "按危险废物/生物废物/锐器废物类别、标签和容器要求收集，交由本单位合规流程处置。"
    return "如产生废弃物，按SDS、本单位EHS分类和标签要求收集处置。"


def infer_first_aid(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["first aid", "exposure", "medical", "wash", "flush"]):
        return "发生暴露后立即停止操作，冲洗/脱除污染物并按本单位流程就医和报告。"
    return "发生人员暴露或不适时立即停止操作、撤离风险源并联系导师/EHS/医疗支持。"


def infer_emergency(text: str) -> str:
    lowered = text.lower()
    if any(k in lowered for k in ["spill", "release", "emergency", "fire"]):
        return "泄漏、火灾或失控释放时优先人员撤离、隔离区域、报警并联系EHS/应急人员。"
    return "异常、泄漏、设备失效或失控反应时立即升级给PI、实验室负责人和EHS。"


def write_seed_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(SOURCES[0]).keys()))
        writer.writeheader()
        for src in SOURCES:
            writer.writerow(asdict(src))


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def write_reports(
    *,
    md_path: Path,
    json_path: Path,
    csv_path: Path,
    seed_path: Path,
    artifact_dir: Path,
    source_stats: list[dict[str, object]],
    rows: list[dict[str, str]],
) -> None:
    md_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "purpose": "external_public_authoritative_lab_safety_ingest",
        "source_count": len(source_stats),
        "row_count": len(rows),
        "csv_path": str(csv_path),
        "seed_path": str(seed_path),
        "artifact_dir": str(artifact_dir),
        "sources": source_stats,
    }
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 外部公开权威实验室安全资料采集报告",
        "",
        f"- generated_at: `{payload['generated_at']}`",
        f"- source_count: `{payload['source_count']}`",
        f"- generated_rows: `{payload['row_count']}`",
        f"- output_csv: `{csv_path}`",
        f"- seed_csv: `{seed_path}`",
        f"- raw_artifacts: `{artifact_dir}`",
        "",
        "## 口径说明",
        "",
        "本报告对应的是从 OSHA、NIH、CDC/NIH、NCBI Bookshelf 和高校 EHS 等公开权威来源新增采集的数据。",
        "它不同于 `release_exports/v9_original_claim_3000/knowledge_base_import_ready_3000.csv` 的长文档语义切分包；后者只改善检索粒度，不能作为新增独立外部数据来源证明。",
        "",
        "## 来源统计",
        "",
        "| source_id | org | type | status | extracted_chars | generated_rows | url |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for stat in source_stats:
        lines.append(
            f"| {stat['id']} | {stat['org']} | {stat.get('content_type','')} | {stat['status']} | "
            f"{stat.get('extracted_chars',0)} | {stat.get('rows',0)} | {stat['url']} |"
        )
    lines.extend(
        [
            "",
            "## 后续建议",
            "",
            "1. 先导入为单独 Dify Dataset：`实验室安全知识库-外部权威来源扩展版`，不要覆盖原 398 条主知识库。",
            "2. 对 `status=external_draft` 的条目进行人工 EHS 审核，审核通过后再合并到正式知识库。",
            "3. 若申报书坚持 3000+ 规模，应继续按本脚本方式扩大来源，而不是拆分旧数据凑数。",
        ]
    )
    md_path.write_text("\n".join(lines), encoding="utf-8")


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit-sources", type=int, default=0, help="Only process first N sources.")
    parser.add_argument("--min-rows", type=int, default=200, help="Warn if generated rows are below this number.")
    parser.add_argument("--output-dir", default="release_exports/v10_external_sources")
    parser.add_argument("--artifact-dir", default="artifacts/web_ingest_public_20260429")
    args = parser.parse_args(list(argv) if argv is not None else None)

    output_dir = (REPO_ROOT / args.output_dir).resolve()
    artifact_dir = (REPO_ROOT / args.artifact_dir).resolve()
    raw_dir = artifact_dir / "raw"
    text_dir = artifact_dir / "extracted_text"
    text_dir.mkdir(parents=True, exist_ok=True)

    seed_path = (REPO_ROOT / "data_sources/public_lab_safety_sources_v1.csv").resolve()
    csv_path = output_dir / "knowledge_base_external_import_ready.csv"
    md_path = output_dir / "import_bundle_report_external.md"
    json_path = output_dir / "import_bundle_report_external.json"

    write_seed_csv(seed_path)

    selected = SOURCES[: args.limit_sources] if args.limit_sources else SOURCES
    rows: list[dict[str, str]] = []
    source_stats: list[dict[str, object]] = []
    seen_rows: set[str] = set()

    for source in selected:
        stat: dict[str, object] = {"id": source.id, "org": source.org, "url": source.url, "status": "pending"}
        try:
            blob, ctype, raw_path = download(source, raw_dir)
            text = extract_text_for_source(source, blob, ctype, raw_path, text_dir)
            text_path = text_dir / f"{source.id}.txt"
            sections = split_sections(text, source)
            made = 0
            for idx, (section_title, section_body) in enumerate(sections, 1):
                row = row_for(source, idx, section_title, section_body)
                dedupe = hashlib.sha256(
                    f"{row['source_url']}|{row['question']}|{row['answer'][:300]}".encode("utf-8")
                ).hexdigest()
                if dedupe in seen_rows:
                    continue
                seen_rows.add(dedupe)
                rows.append(row)
                made += 1
            stat.update(
                {
                    "status": "ok",
                    "content_type": ctype,
                    "raw_path": str(raw_path),
                    "text_path": str(text_path),
                    "extracted_chars": len(text),
                    "sections": len(sections),
                    "rows": made,
                }
            )
            print(f"[ok] {source.id}: chars={len(text)} rows={made}")
        except Exception as exc:  # Keep remaining sources running.
            stat.update({"status": "failed", "error": f"{type(exc).__name__}: {exc}", "rows": 0})
            print(f"[warn] {source.id} failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        source_stats.append(stat)

    write_csv(csv_path, rows)
    write_reports(
        md_path=md_path,
        json_path=json_path,
        csv_path=csv_path,
        seed_path=seed_path,
        artifact_dir=artifact_dir,
        source_stats=source_stats,
        rows=rows,
    )

    print("[done] external public-source ingest completed")
    print(f"- sources: {len(source_stats)}")
    print(f"- rows: {len(rows)}")
    print(f"- csv: {csv_path}")
    print(f"- report: {md_path}")
    if len(rows) < args.min_rows:
        print(f"[warn] generated rows below target: {len(rows)} < {args.min_rows}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
