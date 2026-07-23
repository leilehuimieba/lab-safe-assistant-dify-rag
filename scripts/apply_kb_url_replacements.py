#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import TypedDict

REPO_ROOT = Path(__file__).resolve().parents[1]

class Replacement(TypedDict, total=False):
    url: str
    reason: str
    source_title: str
    source_org: str
    field_updates: dict[str, str]


def replacement(url: str, reason: str, source_title: str = "", source_org: str = "") -> Replacement:
    data: Replacement = {"url": url, "reason": reason}
    if source_title:
        data["source_title"] = source_title
    if source_org:
        data["source_org"] = source_org
    return data


EXACT_REPLACEMENTS: dict[str, Replacement] = {
    "https://ehs.cornell.edu/environmental-compliance/hazardous-waste": replacement(
        "https://ehs.cornell.edu/manuals/hazardous-waste-manual",
        "Cornell EHS hazardous waste page moved to the current Hazardous Waste Manual.",
    ),
    "https://ehs.cornell.edu/research-safety/chemical-safety/chemical-waste": replacement(
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-10-hazardous-chemical-waste",
        "Cornell EHS chemical waste page moved to Laboratory Safety Manual Chapter 10.",
    ),
    "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices": replacement(
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and",
        "Cornell EHS 16.6 Heat and Heating Devices slug changed.",
    ),
    "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164-compressed-gases": replacement(
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164",
        "Cornell EHS 16.4 Compressed Gases slug changed.",
    ),
    "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1612-glass-under-vacuum": replacement(
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1612-glass",
        "Cornell EHS 16.12 Glass Under Vacuum slug changed.",
    ),
    "https://ehs.cornell.edu/research-safety/general-laboratory-safety/laboratory-safety-manual/chapter-4-administrative-controls/47": replacement(
        "https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-4-administrative-controls/47",
        "Cornell EHS Working Alone chapter is under Chemical Safety Laboratory Safety Manual.",
    ),
    "https://cem.com/why-can-t-i-use-a-home-microwave-for-acid-digestion": replacement(
        "https://cem.com/why-can-t-i-use-a-home-microwave-for-acid-digestion-or-extraction",
        "CEM article slug changed.",
    ),
    "https://www.metrohm.com/en/products/ion-chatography/usp-monographs-using-ion-chromatography.html": replacement(
        "https://www.metrohm.com/en/products/ion-chromatography/usp-monographs-using-ion-chromatography.html",
        "Metrohm URL contained a chromatography spelling error.",
    ),
    "https://www.shimadzu.com/an/products/elemental-analysis/atomic-absorption-spectroscopy/aa-7000/index.html": replacement(
        "https://www.shimadzu.com.sg/an/products/elemental-analysis/atomic-absorption-spectroscopy/aa-7000/index.html",
        "Shimadzu global product URL moved; Asia Pacific official page carries the AA-7000 safety section.",
    ),
    "https://www.perkinelmer.com/libraries/gde-nexion-5000-icp-ms-preparing-your-lab.html": replacement(
        "https://www.perkinelmer.com/Nexion-5000-Other-resources",
        "PerkinElmer NexION 5000 guide URL moved to the current resources page.",
    ),
    "https://www.tuttnauer.com/autoclave-troubleshooting": replacement(
        "https://tuttnauer.com/us/support/faq-office-products",
        "Tuttnauer troubleshooting page moved to the official support FAQ.",
    ),
    "https://www.tuttnauer.com/autoclave-maintenance": replacement(
        "https://tuttnauer.com/sites/default/files/2021-10/Manual-Autoclaves-Cleaning_Weekly.pdf",
        "Tuttnauer maintenance page moved; official weekly cleaning PDF preserves maintenance instructions.",
    ),
    "https://ehs.stonybrook.edu/resources/our-policies/Laboratory%20Hood%20Safety.pdf": replacement(
        "https://ehs.stonybrook.edu/_pdfs/EHS_Policy_4.5_Laboratory_Chemical_Fume_Hood_Safety_Program.pdf",
        "Stony Brook EHS fume hood safety policy PDF moved to the current EHS PDF path.",
        "Stony Brook University Laboratory Chemical Fume Hood Safety Program",
        "Stony Brook University Environmental Health and Safety",
    ),
    "https://kjt.hubei.gov.cn/sydw/portal/kjdt/detail?id=2ac1a9c1-aafb-48ca-8b20-3b5b98ec4e6d": replacement(
        "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EB3B94B543F6E4CD18C044DE6AB64CEC",
        "Replaced provincial mirror returning HTTP 412 with the official national standard full-text disclosure page.",
        "GB 19489-2008 实验室生物安全通用要求",
        "国家标准全文公开系统",
    ),
    "https://std.samr.gov.cn/gb/search/gbDetailed?id=8B5B30B7D7D9A755E040A8C59307480E": replacement(
        "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EB3B94B543F6E4CD18C044DE6AB64CEC",
        "Replaced obsolete standard detail ID with the official national standard full-text disclosure page.",
        "GB 19489-2008 实验室生物安全通用要求",
        "国家标准全文公开系统",
    ),
    "https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7B5E4D4E7E040A8C593074662": replacement(
        "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=6C80C3CF343258529DA8841981A036D1",
        "Replaced obsolete standard detail ID with the official national standard full-text disclosure page.",
        "GB/T 27476.1-2014 检测实验室安全 第1部分：总则",
        "国家标准全文公开系统",
    ),
    "https://std.samr.gov.cn/gb/search/gbDetailed?id=71F772D7B5E5D4E7E040A8C593074662": replacement(
        "https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=8BFEEBBE490CBAC79543F0DAD96F2E2E",
        "Replaced obsolete standard detail ID with the official national standard full-text disclosure page.",
        "GB/T 27476.5-2014 检测实验室安全 第5部分：化学因素",
        "国家标准全文公开系统",
    ),
    "https://sbc.cug.edu.cn/info/1013/1172.htm": replacement(
        "https://sbc.cug.edu.cn/info/1234/3228.htm",
        "China University of Geosciences laboratory hazardous waste rules moved to the current lab safety management section.",
        "实验室危险废弃物安全处置管理办法",
        "中国地质大学（武汉）实验室与设备管理处",
    ),
    "https://ccce.csu.edu.cn/info/1591/7436.htm": {
        "url": "https://ccce.csu.edu.cn/info/1591/7436.htm",
        "reason": "The URL opens with a browser user agent; repaired mojibake extracted content into a concise structured Chinese answer.",
        "source_title": "实验室安全知识-化学化工学院门户网站",
        "source_org": "中南大学化学化工学院",
        "field_updates": {
            "title": "化学实验室气瓶、化学品和消防安全要点",
            "question": "化学实验室安全知识中气瓶、化学品和消防有哪些要点？",
            "answer": "化学实验室应保持整洁有序，严格按技术规程操作；涉及危险物料取样、易燃易爆物品处理等潜在危险工作时应有人陪伴。打开强酸、浓氨水或易挥发溶剂应佩戴防护用品并优先在通风柜中进行，稀释浓硫酸必须将酸分批慢慢加入水中。化学试剂应标签清晰、分类存放，不相容化合物不得混放，易燃易爆试剂应置于通风良好的专用柜，剧毒品实行双人双锁和领用登记。气瓶应阴凉、干燥、远离热源并直立固定，剧毒或可燃、助燃气体应分类隔离并配套防毒和消防器材。实验室应配置适用灭火器并定期检查，易燃液体加热不得使用明火，易燃废液不得倒入下水道，应收集后统一处理。",
            "steps": "保持台面和通道整洁; 危险操作执行双人陪伴; 强酸强碱和挥发性试剂在通风柜内开瓶; 浓硫酸稀释遵循酸入水; 化学品按类别和相容性存放; 易燃易爆试剂限量并入专用柜; 剧毒品双人双锁登记; 气瓶直立固定并远离热源; 定期检查灭火器和电气线路; 易燃废液用专用容器收集",
            "ppe": "工作服; 防护眼镜; 防化手套; 必要时使用防毒口罩",
            "forbidden": "禁止实验室内吸烟进食; 禁止水倒入浓硫酸; 禁止明火加热易燃液体; 禁止不相容化学品混放; 禁止易燃废液倒入下水道; 禁止气瓶靠近热源或无固定使用",
        },
    },
    "https://www.eppendorf.com/product-support/centrifugation/": replacement(
        "https://www.eppendorf.com/ae-en/lab-academy/life-science/cell-biology/how-to-clean-a-centrifuge-maintenance-tips/",
        "Replaced dead Eppendorf centrifugation support landing page with current Eppendorf centrifuge maintenance guidance.",
        "How to clean a centrifuge: maintenance tips",
        "Eppendorf",
    ),
    "https://www.mt.com/cn/zh/home/supportive_content/matchar_apps/MatChar_UC345.html": replacement(
        "https://www.tainstruments.com/applications-notes/thermogravimetry-of-air-sensitive-materials/",
        "METTLER TOLEDO regional article URL returned HTTP 406; replaced with an open TGA air-sensitive sample glovebox application note.",
        "Thermogravimetry of Air Sensitive Materials",
        "TA Instruments",
    ),
    "https://www.mt.com/ch/it/home/library/usercoms/lab-analytical-instruments/thermal-analysis-usercom-34.html": {
        "url": "https://www.tainstruments.com/applications-notes/thermogravimetry-of-air-sensitive-materials/",
        "reason": "METTLER TOLEDO UserCom page remained blocked to script/browser-independent audit; replaced with an open TGA air-sensitive sample glovebox application note.",
        "source_title": "Thermogravimetry of Air Sensitive Materials",
        "source_org": "TA Instruments",
        "field_updates": {
            "title": "TGA手套箱内空气敏感样品安全操作",
            "question": "热重分析TGA空气敏感样品如何安全测试？",
            "answer": "对于易与氧气、水分或氮气反应的空气敏感材料，TGA样品制备、自动进样等待和测试过程应尽量保持在惰性环境中。常规惰性吹扫只能降低暴露风险，极敏感样品通常需要将TGA或关键样品处理环节布置在手套箱内，以避免短时暴露造成反应、数据失真或危险副产物。",
            "steps": "测试前评估样品对氧气、水分、氮气的敏感性; 优先在氩气或氮气手套箱内称样和装样; 确认TGA电源、吹扫气、水冷和通讯穿舱连接可靠; 限制样品在自动进样盘或开放环境中的暴露时间; 对含氟锂盐等水敏材料评估水解产生HF等副产物风险; 测试后按样品SOP处理坩埚和残渣",
            "hazard_types": "空气敏感物质暴露后反应; 水分影响热重测试结果; 惰性气氛失效; 手套箱内设备安装与穿舱连接风险",
        },
    },
    "https://www.ugent.be/beton/en/documentation/bead/bet-instrumentation": replacement(
        "https://micromeritics.com/resources/liquid-nitrogen-level-when-using-isothermal-jackets/",
        "Ghent BET instrumentation page returned HTTP 404; replaced with Micromeritics gas sorption liquid-nitrogen safety guidance.",
        "Liquid Nitrogen Level When Using Isothermal Jackets",
        "Micromeritics",
    ),
    "https://hcbi.fas.harvard.edu/sites/projects.iq.harvard.edu/files/hcbidoug/files/chemical_hygiene_plan.pdf": replacement(
        "https://research.harvard.edu/research-policies-compliance/lab-safety/",
        "Harvard chemical hygiene plan PDF URL returned HTTP 404; replaced with Harvard Research lab safety page that links current lab safety policies.",
        "Lab Safety",
        "Harvard University Office of the Vice Provost for Research",
    ),
    "https://www.okonrecycling.com/specialty-equipment-recycling/other-equipments/safe-spectrometer-magnet-disposal/": replacement(
        "https://www.weizmann.ac.il/ChemicalResearchSupport/sites/ChemicalResearchSupport/files/bruker_magnet_safety_0.pdf",
        "Dead third-party NMR magnet disposal article replaced with Bruker/Spectrospin NMR magnet safety notes PDF.",
        "Magnet Safety Notes",
        "Bruker / Spectrospin",
    ),
    "https://www.thermofisher.com/us/en/home/about-us/sustainability/safety.html": replacement(
        "https://documents.thermofisher.com/TFS-Assets/LED/manuals/50155784-c-Thermo%20Scientific%20Sorvall%20ST%2016R-en.pdf",
        "Dead Thermo Fisher generic safety page replaced with an official Thermo Scientific centrifuge operating manual.",
        "Thermo Scientific Sorvall ST 16R Operating Manual",
        "Thermo Fisher Scientific",
    ),
    "https://www.renishaw.com/resourcecentre/download?data=115688&lang=en&userLanguage=en": {
        "url": "https://www.birmingham.ac.uk/documents/college-eps/chemical/science-city/brochure-br010en-03-a-invia-confocal-raman-microscope-1.pdf",
        "reason": "Renishaw resourcecentre download returned HTTP 404; replaced with an accessible Renishaw inVia brochure mirror that includes the laser safety classification text.",
        "source_title": "inVia research-grade confocal Raman microscopes brochure",
        "source_org": "Renishaw brochure mirror hosted by University of Birmingham",
        "field_updates": {
            "title": "Renishaw inVia拉曼显微镜激光安全分类",
            "question": "Renishaw inVia拉曼显微镜激光安全等级如何理解？",
            "answer": "Renishaw inVia Raman microscope 配备激光安全联锁和可选样品罩。其激光安全等级取决于具体配置和所用激光，可能为 Class 1、Class 3B 或 Class 4。使用前应以本机铭牌、配置文件和所在单位激光安全管理要求为准，确认联锁和样品罩有效，未经授权不得拆除防护罩或绕过联锁；Class 3B/4 配置应按高等级激光设备管理，限制人员进入并佩戴匹配波长和功率的激光防护眼镜。",
            "steps": "核对设备铭牌和激光配置; 确认安全联锁和样品罩有效; 使用前完成激光安全培训; 根据Class 1/3B/4等级设置区域管控; 对Class 3B或Class 4配置佩戴匹配护目镜; 禁止打开防护罩直视光路; 维护或调光仅由授权人员执行",
            "ppe": "按激光波长和功率匹配的激光防护眼镜; 实验服; 必要时使用遮光屏或样品罩",
            "forbidden": "禁止绕过激光联锁; 禁止未授权打开光路或防护罩; 禁止直视激光或镜面反射; 禁止按Class 1习惯管理Class 3B/Class 4配置",
        },
    },
    "https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-cryogen-safety.pdf": replacement(
        "https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf",
        "NIH ORS compressed gas and cryogen PDF moved to the current guidelines document URL.",
        "NIH Compressed Gas and Cryogen Safety Guidelines",
        "NIH ORS",
    ),
    "https://ors.od.nih.gov/sr/dohs/safety/compressed-gas-cryogen-safety.pdf": replacement(
        "https://ors.od.nih.gov/sr/dohs/Documents/compressed-gas-and-cryogen-safety-guidelines-document.pdf",
        "NIH ORS compressed gas and cryogen PDF moved from the old safety path to the current guidelines document URL.",
        "NIH Compressed Gas and Cryogen Safety Guidelines",
        "NIH ORS",
    ),
    "https://ors.od.nih.gov/sr/dohs/safety/laser/Pages/default.aspx": replacement(
        "https://ors.od.nih.gov/sr/dohs/Documents/laser-safety-program.pdf",
        "NIH ORS laser safety program page moved; replaced with the current NIH Laser Safety Program PDF.",
        "NIH Laser Safety Program",
        "NIH ORS",
    ),
    "https://www.epa.gov/hw/hazardous-waste-container-management-requirements": replacement(
        "https://iwaste.epa.gov/rpts/handbk4.pdf",
        "EPA hazardous waste container management page returned HTTP 404; replaced with EPA's Hazardous Waste Containers handbook PDF.",
        "Hazardous Waste Containers",
        "U.S. Environmental Protection Agency",
    ),
    "https://www.epa.gov/chemical-safety/nanotechnology-research-and-applications": {
        "url": "https://www.epa.gov/reviewing-new-chemicals-under-toxic-substances-control-act-tsca/control-nanoscale-materials-under",
        "reason": "EPA nanotechnology research page returned HTTP 404; replaced with EPA's current nanoscale materials TSCA control page and narrowed the answer to supported regulatory framing.",
        "source_title": "Control of Nanoscale Materials under the Toxic Substances Control Act",
        "source_org": "U.S. Environmental Protection Agency",
        "field_updates": {
            "title": "纳米材料废物管理的法规判定口径",
            "question": "纳米材料废物应如何进行合规判定？",
            "answer": "阶段4_废弃物物理标准\r\n\r\n纳米材料废物不能因为尺寸小就默认按普通固废处理。EPA 将许多纳米尺度材料视为 TSCA 下的化学物质；进入废物流后，还应按 RCRA 的危险废物识别框架，结合材料本体化学成分、污染物、毒性/反应性/易燃性/腐蚀性等特性和单位制度进行判定。对碳纳米管、纳米金属氧化物等粉体，应重点控制吸入暴露和泄漏扩散，使用密闭容器收集并保留 SDS/实验记录，交由有资质渠道处置。",
            "steps": "确认纳米材料名称和基础化学组成; 查询SDS和实验污染物; 按RCRA特性和清单判断是否危险废物; 粉体收集时避免扬尘; 使用密闭兼容容器并贴明纳米材料/污染物标签; 保留产生量和处置记录; 交由有资质危废或校内EHS渠道处理",
            "forbidden": "禁止将纳米粉体直接倒入普通垃圾或下水道; 禁止无标签混入普通固废; 禁止干扫造成二次扬尘; 禁止未判定危险特性就自行处置",
        },
    },
    "https://www.epa.gov/hw/hazardous-waste-manifest-system": replacement(
        "https://www.epa.gov/hwgenerators/hazardous-waste-manifest-system",
        "EPA hazardous waste manifest page moved under the Hazardous Waste Generators section.",
        "Hazardous Waste Manifest System",
        "U.S. Environmental Protection Agency",
    ),
    "https://www.epa.gov/hw/hazardous-waste-combustion": {
        "url": "https://archive.epa.gov/epawaste/hazard/tsd/td/web/html/combustion.html",
        "reason": "EPA hazardous waste combustion page returned HTTP 404; replaced with EPA's archived hazardous waste combustion overview and narrowed the answer to permitted combustion controls.",
        "source_title": "Combustion - Hazardous Waste",
        "source_org": "U.S. Environmental Protection Agency Archive",
        "field_updates": {
            "title": "危险废物燃烧处置的合规限制",
            "question": "含有机物或含氟材料的危险废物可以直接燃烧处理吗？",
            "answer": "阶段4_废弃物物理标准\r\n\r\n危险废物不得在普通炉具、通风柜或实验室内自行焚烧。EPA 对危险废物燃烧设施按焚烧炉、锅炉、工业炉等类别实施管理；焚烧主要用于破坏有机危险成分并降低废物体积，但必须由具备许可和烟气控制能力的设施执行。含氟聚合物、卤代有机物等燃烧可能产生腐蚀性或有毒酸性气体，实验室应作为危险废物分类收集，交由有资质单位按许可路线处理。",
            "steps": "确认废物成分和卤素/含氟组分; 按SDS和危险废物规则分类; 使用兼容容器密闭收集; 标签注明含氟/卤代/有机危险成分; 不在实验室自行加热或焚烧; 交由校内EHS或有资质处置单位处理",
            "forbidden": "禁止在通风柜内焚烧废物; 禁止将含氟聚合物废料按普通垃圾燃烧; 禁止无烟气净化和许可设施处理; 禁止混入不相容废物",
        },
    },
    "https://www.hse.gov.uk/biosafety/infection.htm": replacement(
        "https://www.hse.gov.uk/biosafety/",
        "HSE infection page moved into the current infections and biological hazards at work hub.",
        "Infections and biological hazards at work",
        "HSE UK",
    ),
    "https://www.fda.gov/radiation-emitting-products": replacement(
        "https://www.law.cornell.edu/cfr/text/21/1020.40",
        "Generic FDA radiation-emitting products entry was blocked in automated audit; replaced with an accessible 21 CFR 1020.40 text supporting the XRD/X-ray safety row.",
        "21 CFR 1020.40 - Cabinet x-ray systems",
        "Legal Information Institute / e-CFR",
    ),
    "https://www.fda.gov/regulatory-information/search-fda-guidance-documents/compliance-guide-cabinet-x-ray-systems": replacement(
        "https://www.law.cornell.edu/cfr/text/21/1020.40",
        "FDA cabinet X-ray guidance page triggers automated abuse-detection responses; replaced with an accessible 21 CFR 1020.40 text.",
        "21 CFR 1020.40 - Cabinet x-ray systems",
        "Legal Information Institute / e-CFR",
    ),
    "https://www.thermofisher.com/blog/materials/a-safer-smarter-alternative-for-ftir-spectroscopy-exploring-thermoelectrically-cooled-mct-detectors/": replacement(
        "https://documents.thermofisher.com/TFS-Assets/CAD/Application-Notes/apex-te-mct-an64724-en.pdf",
        "Thermo Fisher blog returned HTTP 404 to automated audit; replaced with an official Thermo Fisher TEC-MCT detector application note PDF.",
        "Thermoelectrically cooled MCT detectors enable high speed and high sensitivity FTIR gas analysis",
        "Thermo Fisher Scientific",
    ),
    "https://www.thermofisher.com/blog/materials/analysis-of-smoke-toxicity-using-ftir-spectroscopy-webinar/": replacement(
        "https://documents.thermofisher.com/TFS-Assets/MSD/Technical-Notes/FL53370-gas-phase-ftir-smoke-toxicity-measurements.pdf",
        "Thermo Fisher smoke-toxicity webinar URL returned HTTP 404 to automated audit; replaced with the official Thermo Fisher gas-phase FTIR smoke toxicity technical note PDF.",
        "Gas-phase FTIR for smoke toxicity measurements",
        "Thermo Fisher Scientific",
    ),
    "https://knowledge1.thermofisher.com/@api/deki/files/29093/Ver_1.02_-_iCAP_7000_Reference_Guide.pdf": replacement(
        "https://knowledge1.thermofisher.com/Trace_Elemental_Analysis/Inductively_Coupled_Plasma_-_Optical_Emission_Spectroscopy_ICP-OES/iCAP_Operator_Manuals/BRE0004150_-_iCAP_7000_Series_Operating_Manual_Rev_C",
        "Thermo Fisher file API timed out in automated audit; replaced with the official Thermo Fisher Knowledge article for the same iCAP 7000 operating manual.",
        "BRE0004150 - iCAP 7000 Series Operating Manual Rev C",
        "Thermo Fisher Scientific",
    ),
    "https://products.metrohm.com/eps/930-compact-ic-flex-6132": replacement(
        "https://www.metrohm.com/content/dam/metrohm/shared/documents/manuals/89/89308001EN.pdf",
        "Metrohm products subdomain has a certificate hostname mismatch; replaced with the official Metrohm 930 Compact IC Flex manual PDF path.",
        "930 Compact IC Flex Manual",
        "Metrohm",
    ),
}


def compact(text: object) -> str:
    return str(text or "").strip()


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader.fieldnames or []), list(reader)


def canonicalize_url(url: str) -> Replacement | None:
    if url in EXACT_REPLACEMENTS:
        return EXACT_REPLACEMENTS[url]
    if url.startswith("http://www.osha.gov/"):
        return replacement("https://www.osha.gov/" + url[len("http://www.osha.gov/") :], "OSHA canonical HTTPS URL.")
    return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Apply audited source URL replacements to knowledge_base_curated.csv")
    parser.add_argument("--kb", default=str(REPO_ROOT / "knowledge_base_curated.csv"))
    parser.add_argument("--report-dir", default=str(REPO_ROOT / "artifacts/kb_traceability_20260718"))
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--updated-at", default=date.today().isoformat())
    parser.add_argument(
        "--export-register",
        action="store_true",
        help="Export a cumulative replacement register by comparing --before-kb and --kb.",
    )
    parser.add_argument(
        "--before-kb",
        default=str(REPO_ROOT / "artifacts/kb_traceability_20260718/knowledge_base_curated.before_metadata_fix.csv"),
    )
    parser.add_argument("--run-id", default="")
    return parser.parse_args()


REPORT_FIELDS = [
    "id",
    "title",
    "old_url",
    "new_url",
    "old_source_title",
    "new_source_title",
    "old_source_org",
    "new_source_org",
    "reason",
]


def replacement_report_row(old_row: dict[str, str], new_row: dict[str, str], replacement_data: Replacement) -> dict[str, str]:
    return {
        "id": compact(new_row.get("id")) or compact(old_row.get("id")),
        "title": compact(new_row.get("title")) or compact(old_row.get("title")),
        "old_url": compact(old_row.get("source_url")),
        "new_url": compact(new_row.get("source_url")),
        "old_source_title": compact(old_row.get("source_title")),
        "new_source_title": compact(new_row.get("source_title")),
        "old_source_org": compact(old_row.get("source_org")),
        "new_source_org": compact(new_row.get("source_org")),
        "reason": replacement_data["reason"],
    }


def export_replacement_register(before_kb: Path, current_kb: Path, report_dir: Path) -> Path:
    _, before_rows = read_csv(before_kb)
    _, current_rows = read_csv(current_kb)
    before_by_id = {compact(row.get("id")): row for row in before_rows if compact(row.get("id"))}
    register_rows: list[dict[str, str]] = []

    for current in current_rows:
        row_id = compact(current.get("id"))
        before = before_by_id.get(row_id)
        if not before:
            continue
        old_url = compact(before.get("source_url"))
        current_url = compact(current.get("source_url"))
        replacement_data = canonicalize_url(old_url)
        if not replacement_data:
            continue
        if replacement_data["url"] != current_url:
            continue
        register_rows.append(replacement_report_row(before, current, replacement_data))

    report_path = report_dir / "kb_url_replacements_register_20260718.csv"
    with report_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(register_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "before_kb": str(before_kb),
        "current_kb": str(current_kb),
        "changed_row_count": len(register_rows),
        "unique_old_url_count": len({row["old_url"] for row in register_rows}),
        "unique_new_url_count": len({row["new_url"] for row in register_rows}),
        "report_csv": str(report_path),
    }
    (report_dir / "kb_url_replacements_register_20260718_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return report_path


def main() -> int:
    args = parse_args()
    kb_path = Path(args.kb).resolve()
    report_dir = Path(args.report_dir).resolve()
    report_dir.mkdir(parents=True, exist_ok=True)

    if args.export_register:
        report = export_replacement_register(Path(args.before_kb).resolve(), kb_path, report_dir)
        print(f"[done] replacement_register={report}")
        return 0

    headers, rows = read_csv(kb_path)

    changed_rows = []
    for row in rows:
        original_row = dict(row)
        old_url = compact(row.get("source_url"))
        replacement_data = canonicalize_url(old_url)
        if not replacement_data:
            continue
        new_url = replacement_data["url"]
        reason = replacement_data["reason"]
        old_source_title = compact(row.get("source_title"))
        old_source_org = compact(row.get("source_org"))
        new_source_title = replacement_data.get("source_title", "")
        new_source_org = replacement_data.get("source_org", "")
        row["source_url"] = new_url
        for field in ("references", "legal_notes"):
            current = compact(row.get(field))
            if not current:
                continue
            if old_url and old_url in current:
                current = current.replace(old_url, new_url)
            if new_source_title and old_source_title and old_source_title in current:
                current = current.replace(old_source_title, new_source_title)
            if new_source_org and old_source_org and old_source_org in current:
                current = current.replace(old_source_org, new_source_org)
            row[field] = current
        if new_source_title:
            row["source_title"] = new_source_title
        if new_source_org:
            row["source_org"] = new_source_org
        for field, value in replacement_data.get("field_updates", {}).items():
            if field in row:
                row[field] = value
        if "last_updated" in row:
            row["last_updated"] = args.updated_at
        if row == original_row:
            continue
        changed_rows.append(replacement_report_row(original_row, row, replacement_data))

    mode = "dry_run" if args.dry_run else "applied"
    run_id = args.run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_csv = report_dir / f"kb_url_replacements_{mode}_{run_id}.csv"
    latest_report_csv = report_dir / f"kb_url_replacements_{mode}.csv"
    with report_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(changed_rows)
    with latest_report_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REPORT_FIELDS)
        writer.writeheader()
        writer.writerows(changed_rows)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dry_run": args.dry_run,
        "changed_row_count": len(changed_rows),
        "unique_old_url_count": len({row["old_url"] for row in changed_rows}),
        "report_csv": str(report_csv),
    }
    summary_path = report_dir / f"kb_url_replacements_{mode}_{run_id}_summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    (report_dir / f"kb_url_replacements_{mode}_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if not args.dry_run:
        with kb_path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

    print(f"[done] dry_run={args.dry_run} changed_rows={len(changed_rows)} unique_old_urls={summary['unique_old_url_count']}")
    print(f"[done] report={report_csv}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
