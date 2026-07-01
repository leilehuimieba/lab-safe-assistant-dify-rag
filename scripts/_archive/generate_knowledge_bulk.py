#!/usr/bin/env python3
"""批量知识库条目生成器 v2 —— 数据驱动方式，从化学品/设备/场景表自动生成 QA 对。

用法：python scripts/generate_knowledge_bulk.py
输出追加到 knowledge_base_curated.csv
"""

from __future__ import annotations

import csv
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
KB_FILE = REPO_ROOT / "knowledge_base_curated.csv"
TODAY = datetime.now().strftime("%Y-%m-%d")

HEADERS = [
    "id", "title", "category", "subcategory", "lab_type", "risk_level",
    "hazard_types", "scenario", "question", "answer", "steps", "ppe",
    "forbidden", "disposal", "first_aid", "emergency", "legal_notes",
    "references", "source_type", "source_title", "source_org",
    "source_version", "source_date", "source_url", "last_updated",
    "reviewer", "status", "tags", "language",
]

_ID_SEQ = 7000


def _next_id(prefix: str = "KB-GEN") -> str:
    global _ID_SEQ
    _ID_SEQ += 1
    return f"{prefix}-{_ID_SEQ}"


def _sig(title: str, question: str) -> str:
    return hashlib.md5(f"{title}||{question}".encode()).hexdigest()[:10]


# ══════════════════════════════════════════
# 数据表
# ══════════════════════════════════════════

# --- 常见实验室化学品 MSDS 数据 ---
CHEMICALS = [
    # (中文名, 英文名, 危害类型, 风险等级, 特殊注意事项)
    ("甲醇", "Methanol", "易燃;有毒;挥发性", "4", "吸入或皮肤吸收可致中毒（视神经损伤），代谢产生甲醛和甲酸"),
    ("甲苯", "Toluene", "易燃;刺激性;生殖毒性", "3", "长期接触可能影响神经系统;孕妇避免接触"),
    ("正己烷", "n-Hexane", "易燃;神经毒性;挥发性", "4", "长期吸入可致周围神经病变;通风柜内使用"),
    ("苯", "Benzene", "易燃;致癌(IARC 1类);血液毒性", "5", "骨髓毒性;严禁皮肤接触和吸入;孕妇禁用"),
    ("苯酚", "Phenol", "腐蚀性;有毒;经皮吸收", "4", "皮肤大面积接触可致死;必须佩戴防渗透手套"),
    ("氨水", "Ammonium Hydroxide", "腐蚀性;刺激性气体;环境危害", "3", "释放氨气刺激性极强;与酸混合放热;通风柜操作"),
    ("冰醋酸", "Glacial Acetic Acid", "腐蚀性;易燃;刺激性", "3", "凝固点16.7°C;低温时可能结晶;可燃"),
    ("磷酸", "Phosphoric Acid", "腐蚀性;刺激性", "2", "中等强度酸;高温分解产生有毒磷氧化物"),
    ("高氯酸", "Perchloric Acid", "强氧化剂;爆炸;腐蚀性", "5", "与有机物接触可爆炸;需专用通风柜（带水冲洗系统）;严格控制用量"),
    ("氢氟酸", "Hydrofluoric Acid", "剧毒;腐蚀性;经皮吸收", "5", "氟离子可穿透皮肤深层腐蚀骨骼;中毒后需葡萄糖酸钙凝胶急救;极度危险"),
    ("三氯甲烷", "Chloroform", "有毒;致癌;挥发性", "4", "卤代溶剂;光照分解产生光气;含乙醇稳定剂"),
    ("四氢呋喃", "THF", "易燃;过氧化物形成;刺激性", "4", "长期储存形成爆炸性过氧化物;使用前测试;不可蒸干"),
    ("吡啶", "Pyridine", "易燃;有毒;恶臭;刺激性", "3", "极难闻;通风柜内操作;皮肤可吸收"),
    ("丙烯酰胺", "Acrylamide", "神经毒性;致癌;可疑生殖毒性", "4", "固体粉末不可吸入;溶液操作在通风柜内;聚合放热"),
    ("N,N-二甲基甲酰胺", "DMF", "易燃;生殖毒性;经皮吸收", "4", "皮肤可渗透;孕妇禁用;通风柜使用"),
    ("二甲亚砜", "DMSO", "经皮吸收促进剂;刺激性", "2", "可将溶解的化学物质带入体内;处理含毒DMSO溶液时需加强防护"),
    ("三乙胺", "Triethylamine", "易燃;腐蚀性;恶臭;刺激性", "3", "鱼腥味极强;腐蚀铝;蒸气刺激眼睛"),
    ("正丁醇", "n-Butanol", "易燃;刺激性", "2", "较高沸点;蒸气对眼睛有刺激性;与水部分混溶"),
    ("环己烷", "Cyclohexane", "易燃;刺激性;环境危害", "3", "对水生生物有害;挥发性强"),
    ("乙酸乙酯", "Ethyl Acetate", "易燃;刺激性;挥发性", "2", "常用萃取溶剂;有水果味但不可吸入;闪点-4°C"),
    ("石油醚", "Petroleum Ether", "极易燃;神经毒性;挥发性", "4", "混合烃;闪点极低;蒸气可远距离引燃"),
    ("异丙醇", "Isopropanol", "易燃;刺激性", "2", "常用消毒剂;高浓度蒸气可致头晕;远离热源"),
    ("丁酮", "MEK", "易燃;刺激性;生殖毒性", "3", "孕妇避免接触;强溶剂可渗透手套"),
    ("丙三醇", "Glycerol", "低毒;粘稠", "1", "无毒但高温分解释放丙烯醛;加热时通风"),
    ("亚硝酸钠", "Sodium Nitrite", "氧化剂;有毒;环境危害", "3", "可形成致癌亚硝胺;摄入可致高铁血红蛋白血症"),
    ("重铬酸钾", "Potassium Dichromate", "强氧化剂;致癌;环境危害", "5", "六价铬强致癌物;含铬废液单独收集;手套+通风柜"),
    ("高锰酸钾", "Potassium Permanganate", "强氧化剂;腐蚀性;环境危害", "3", "与有机物/还原剂剧烈反应;避免接触皮肤（染棕色斑）"),
    ("氰化钠/氰化钾", "Sodium/Potassium Cyanide", "剧毒;环境危害", "5", "与酸接触释放HCN剧毒气体;双人双锁管理;专用解毒剂（亚硝酸异戊酯+硫代硫酸钠）"),
    ("汞", "Mercury", "剧毒;神经毒性;环境持久", "5", "常温挥发汞蒸气;泄漏用硫粉或专用吸收剂;禁止使用吸尘器;定期测汞蒸气浓度"),
    ("钠", "Sodium metal", "遇水反应;易燃;腐蚀性", "5", "遇水剧烈反应产生H₂并可能燃烧;存放于煤油或矿物油中;切割在油下进行"),
    ("氢化铝锂", "LAH", "遇水反应;易燃;腐蚀性", "5", "极强的还原剂;遇水爆炸性反应;仅在无水无氧条件下使用;少量处理"),
    ("硼氢化钠", "Sodium Borohydride", "遇水反应;有毒;腐蚀性", "3", "与水反应释放H₂;使用无水溶剂;不燃但可助燃"),
    ("叔丁基锂", "t-BuLi", "自燃;遇水反应;腐蚀性", "5", "空气中自燃;需严格无氧无水操作(Schlenk line或手套箱);极危险试剂"),
    ("三氟乙酸", "TFA", "腐蚀性;挥发性;有毒", "4", "强腐蚀性（与玻璃反应）;通风柜使用;不可密封存放"),
    ("三氯氧磷", "POCl₃", "腐蚀性;遇水反应;有毒", "4", "与水剧烈反应释放HCl;通风柜操作;干燥环境储存"),
    ("氯化亚砜", "SOCl₂", "腐蚀性;遇水反应;有毒气体", "4", "与水反应释放SO₂和HCl;通风柜操作;破坏呼吸系统"),
]

# --- 常见实验室设备 ---
EQUIPMENT = [
    # (设备名, 类型, 主要风险, 风险等级, 关键安全规则)
    ("旋转蒸发仪", "分离设备", "玻璃器皿内爆;溶剂蒸气;旋转部件", "3", "抽真空前检查玻璃瓶有无裂纹;冷却水/冷阱必须开启;易燃溶剂彻底冷却后释放真空"),
    ("超声波清洗器", "清洗设备", "听力损伤;液体飞溅;气溶胶", "2", "必须盖好盖子再运行;不可超声清洗含易燃溶剂的器皿;佩戴听力防护（持续操作时）"),
    ("磁力搅拌器/加热搅拌器", "通用设备", "烫伤;磁子飞溅;电气故障", "2", "加热功能使用后关闭并标注;加热液体的温度需监控;磁子不可用于高粘度液体"),
    ("微波消解仪", "样品前处理", "高压爆炸;高温烫伤;微波辐射", "4", "严格按SOP称样量和消解程序;不可消解未知样品;消解罐定期更换;操作时戴面罩"),
    ("激光器", "光学设备", "眼损伤;皮肤烧伤;火灾;高压电", "5", "激光安全等级标识;对应波长防护镜;光学平台周围设置隔断或警示区;钥匙管理"),
    ("手套箱", "惰性气氛设备", "缺氧;化学品暴露;压力", "3", "手套不得有破损;真空/惰性气体置换程序规范;溶剂不可大量进入箱内;再生催化剂定期维护"),
    ("气相色谱仪", "分析仪器", "高温烫伤;高压气体;易燃氢气", "3", "使用FID时氢气安全：防泄漏、使用后关闭;进样口高温不可触摸;气体管路定期检漏"),
    ("高效液相色谱仪(HPLC)", "分析仪器", "高压泵;有机溶剂;紫外辐射", "2", "流动相废液收集;柱压异常时停机检查;乙腈/甲醇等流动相在通风柜配制"),
    ("原子吸收光谱仪(AAS)", "分析仪器", "高温;可燃气体(乙炔);紫外辐射", "4", "乙炔气瓶安全;火焰传感器正常;排风正常（燃烧产物需排出）"),
    ("核磁共振波谱仪(NMR)", "大型仪器", "强磁场;低温液体(液氮/液氦);失超风险", "4", "心脏起搏器/金属植入物禁止靠近;铁磁物体禁止进入磁体室;失超时立即撤离"),
    ("X射线衍射仪(XRD)", "分析仪器", "X射线辐射;高压电", "4", "安全联锁装置不得旁路;辐射剂量计佩戴;防护罩关闭后方可出束"),
    ("生物安全柜", "生物安全设备", "生物气溶胶;紫外辐射;HEPA堵塞", "3", "Ⅱ级BSC是最常用类型;操作前后运行5分钟净化;紫外灯仅在无人时开启;HEPA定期检测"),
    ("超净工作台", "洁净设备", "紫外辐射;气流", "1", "与生物安全柜不同——仅保护样品不保护人员;不可用于感染性材料操作"),
    ("液氮罐", "低温储存", "低温冻伤;窒息;爆炸", "4", "液氮补充在通风处进行;罐体不可密封;定期检查真空度;运输时固定"),
    ("制冰机", "通用设备", "电气;微生物污染", "1", "定期清洁消毒;不可用于食品制冰;排水管不得堵死"),
    ("纯水/超纯水机", "通用设备", "电气;微生物;漏水", "1", "定期更换滤芯;长期不用排空;漏水报警正常工作"),
    ("拉曼光谱仪", "分析仪器", "激光辐射;化学品接触", "2", "激光等级确认;防护镜;样品室关闭后测量"),
    ("冷冻干燥机", "样品制备", "真空内爆;低温;化学品暴露", "3", "玻璃瓶完好;冷阱温度足够低;有机溶剂需先挥发大部分再冻干"),
]

# --- 应急场景 ---
EMERGENCY_SCENARIOS = [
    # (场景名, 类型, 具体问题, 答案要点)
    ("地震时实验室应急", "自然灾害", "发生地震时实验室人员应该怎么做？",
     "地震时：1) 立即停止实验，关闭正在进行的危险反应和加热设备;2) 远离化学品架、气瓶、窗户;3) 蹲下护住头部，躲在结实的实验台下;4) 震动停止后有序撤离（不使用电梯）;5) 撤离前关闭水电和气源（安全前提下）;6) 在安全集合点清点人数。特别注意：强震可能导致化学品倾倒泄漏和气瓶倒塌，撤离后不得返回实验室取物品。"),
    ("实验室停电应急处置", "设施故障", "实验室突然停电应该怎么处理？",
     "停电应急处置：1) 立即停止所有实验操作;2) 关闭加热设备和正在反应的实验装置;3) 确认通风柜和生物安全柜停止运行——盖好化学品、关闭前窗;4) 关闭所有气瓶阀门;5) 将低温冰箱/冰柜门保持关闭（不开门可保温数小时）;6) 使用应急照明或手电撤离;7) 联系物业/电工确认停电原因和预计恢复时间;8) 来电后先检查关键设备状态再恢复实验。绝不在停电期间用明火照明。"),
    ("水银温度计打破", "化学品泄漏", "水银温度计打破了应该怎么处理？",
     "水银温度计打破处置：1) 立即疏散该区域人员;2) 关闭空调/风扇防止汞蒸气扩散;3) 开窗通风（如有）;4) 佩戴手套和口罩;5) 用硬纸片或刮板将汞珠聚拢;6) 用专用汞吸收剂或硫粉覆盖（硫粉+汞→硫化汞，降低蒸气压）;7) 用胶带粘取细小汞珠;8) 所有废物（玻璃碎片+汞+吸收剂+手套）作为含汞危废处置;9) 保持通风24小时。禁止使用吸尘器或扫帚（会扩散汞）。"),
    ("实验台酒精灯倾倒起火", "火灾", "实验台上的酒精灯被打翻了着火了怎么办？",
     "酒精灯倾倒起火处置：1) 保持冷静，火势通常可控;2) 用灭火毯覆盖灭火（最佳方法）或用湿布/湿毛巾盖灭;3) 不可用嘴吹——会扩散火焰;4) 不可用水泼——酒精密度低于水，会浮在水面扩散燃烧;5) 若火势蔓延到其他物品，使用干粉灭火器;6) 若有人员衣物着火，让其就地翻滚，用灭火毯覆盖;7) 灭火后通风排烟;8) 报告实验室管理人员。"),
    ("被玻璃器皿割伤", "人员受伤", "实验过程中被玻璃器皿割伤出血了怎么办？",
     "割伤出血处置：1) 立即用清水冲洗伤口去除可能的化学品残留;2) 用无菌纱布或干净布加压止血;3) 将受伤部位抬高（高于心脏）减少出血;4) 较深伤口或出血不止——在伤口上方近心端绑止血带（记录时间，每30-45分钟松1-2分钟）;5) 玻璃碎片留在伤口内不可自行拔出;6) 及时就医评估是否需要破伤风疫苗;7) 记录事故并报告。注意：若不确定是否有化学品进入伤口，务必告知医生实验涉及的化学品。"),
    ("化学品灼伤眼睛", "人员受伤", "强酸或强碱溅到眼睛了怎么办？",
     "化学品眼部灼伤处置：1) 立即前往最近的洗眼器！秒级响应！;2) 用手指强行撑开上下眼睑（最关键的步骤——化学品在眼内每多1秒伤害都加重）;3) 用大量清水/洗眼液持续冲洗至少15-20分钟;4) 冲洗过程中转动眼球各方向，确保全面冲洗;5) 若有隐形眼镜，在冲洗中尽快取出;6) 冲洗后立即就医眼科;7) 带上化学品的SDS/标签供医生参考;8) 禁止揉眼——加重伤害。记住：强碱眼部灼伤比强酸更危险（碱可穿透角膜深层）。"),
    ("液氮大面积泄漏", "化学品泄漏", "液氮罐倒了液氮大面积泄漏怎么办？",
     "液氮大面积泄漏处置：1) 立即疏散该区域所有人员;2) 打开门窗最大程度通风（氮气无色无味，可置换氧气导致窒息）;3) 若空间密闭或通风不良，所有人立即撤离到室外;4) 在确保安全的前提下关闭液氮源;5) 待液氮完全蒸发和空间充分通风后方可返回;6) 注意：液氮泄漏时地面温度极低，不可直接接触。若有人员吸入大量氮气后昏迷，立即转移到通风处并呼叫急救。"),
    ("有机溶剂中毒", "人员受伤", "有人在实验中吸入了大量有机溶剂蒸气出现头晕、恶心怎么办？",
     "有机溶剂吸入中毒处置：1) 立即将中毒者移至通风处（施救者需做好呼吸防护再进入）;2) 松开衣领保持呼吸道通畅;3) 若中毒者清醒：保持坐位或半卧位，保暖;4) 若中毒者昏迷但有呼吸：侧卧位防止窒息;5) 若无呼吸：立即人工呼吸和CPR;6) 呼叫120;7) 告知医生中毒的溶剂名称和大致吸入量;8) 保留溶剂瓶/SDS供医生参考。特别注意：部分有机溶剂中毒有延迟性（如二氯甲烷代谢产生CO，症状可能数小时后出现），必须就医观察。"),
    ("易燃溶剂蒸气爆炸", "爆炸", "实验室闻到浓烈的溶剂味，怀疑有易燃蒸气积聚，怎么办？",
     "怀疑易燃蒸气积聚处置：1) 不要开关任何电器开关（包括电灯、手机、排风扇）——开关电火花可能引爆;2) 不要拔插头;3) 轻声通知周围人员;4) 缓慢离开，不要跑动（防静电）;5) 到安全区域后拨打紧急电话;6) 在专业人员到达前禁止任何人进入。预防措施：所有使用易燃溶剂的实验必须在通风柜内进行;实验区禁止大量敞口存放溶剂。"),
    ("锂离子电池热失控", "设备事故", "正在充电的锂电池设备冒烟了怎么办？",
     "锂电池热失控处置：1) 若电池只是发热尚未冒烟冒火——立即断电（拔插头），将设备移至空旷安全处（室外或防火区域），密切观察;2) 若已冒烟/冒火（热失控已发生）——立即断电，不要试图移动设备，全员撤离;3) 用D类灭火器或干砂覆盖灭火（前提：安全且受过培训）;4) 不可用水（锂与水反应）;5) 不可用ABC干粉（效果有限）;6) 热失控产生的烟雾剧毒，不可吸入;7) 报警并报告;8) 火灾完全扑灭后仍需监控数小时（可能复燃）。"),
]

# --- 废弃物处置场景 ---
WASTE_SCENARIOS = [
    ("废弃过氧化物形成剂处置", "化学危废",
     "长期未用的乙醚或THF瓶中有结晶物怎么办？",
     "过氧化物形成剂（乙醚、THF、异丙醚、二氧六环等）长期存放可形成爆炸性过氧化物结晶。若瓶口或瓶内有可见结晶物：1) 绝对不要移动或开盖！移动/摩擦/开盖可能引发爆炸;2) 立即在瓶上标注「疑似过氧化物—勿动」;3) 隔离区域，疏散附近人员;4) 联系EHS/专业危废处置团队处理;5) 不可自行处理！这是实验室最危险的废弃物之一。预防：此类化学品开瓶后在瓶身标注开瓶日期，6个月后测试过氧化物，12个月后及时处置。"),
    ("含溴乙锭(EB)凝胶废物处置", "生物危废",
     "含EB（或EB替代物）的琼脂糖凝胶怎么处理？",
     "核酸染料（EB及其替代物如GelRed/SYBR Safe等均具有潜在致突变性）不可作为普通垃圾丢弃：1) 固体凝胶收集于专用生物危废袋（标注核酸染料污染）;2) 含染料的电泳缓冲液收集于专用废液桶;3) 污染的枪头、手套等也归入此类;4) 所有含核酸染料的废物按生物/化学混合危废交专业处置;5) 不可倒入下水道;6) 不可直接放入普通垃圾。注意：即使商家声称「安全替代品」也应视为有潜在风险，按危废标准处置。"),
    ("针头和锐器处置", "生物危废",
     "用过的注射器针头和手术刀片应该怎么丢弃？",
     "锐器处置是实验室安全关键环节：1) 所有针头、刀片、碎玻璃、毛细管等锐器必须丢入专用锐器盒;2) 锐器盒应为硬质防穿刺容器，有明显生物危害标识;3) 针头不可回套针帽（回套是针刺伤最常见原因）;4) 锐器盒装至3/4满时密封，不可继续使用;5) 密封后按生物危废处置;6) 若被针头刺伤：立即流水冲洗挤出血液、消毒、就医评估感染风险和暴露后预防。"),
    ("含纳米材料废物处置", "化学危废",
     "含纳米材料（如碳纳米管、纳米银等）的实验废物怎么处理？",
     "纳米材料的毒理学特性尚不完全清楚，处置需格外谨慎：1) 含纳米材料的废液不可倒入下水道;2) 固体纳米材料废物密封包装（双重密封袋）;3) 标注纳米材料种类和浓度;4) 按化学危废处理（目前无专门的纳米废物类别）;5) 操作和处置时佩戴口罩和手套（部分纳米材料可通过呼吸道吸收）;6) 含纳米材料的器皿先擦拭/清洗后再按常规流程洗涤（清洗液作为纳米废液收集）。"),
    ("未知化学品处置", "化学危废",
     "实验室发现无标签的化学品瓶怎么办？",
     "无标签未知化学品是实验室的重大安全隐患：1) 不要随便打开瓶盖——可能挥发有毒/易燃气体或发生反应;2) 不要丢弃——可能产生不相容危废混合;3) 通过实验室台账/采购记录尝试追溯;4) 若无法追溯，联系EHS/专业危废处置进行评估和处置;5) 处置费用可能很高（未知物需分析后才能确定处置方式）;6) 在瓶身标注「未知物待鉴定」;7) 预防：所有试剂瓶必须贴标签（名称、浓度、日期、责任人），每学期清理过期或失效标签的化学品。"),
]

# --- PPE 扩展场景 ---
PPE_SCENARIOS = [
    ("防化手套渗透时间", "手套选择",
     "防化手套的渗透时间是什么意思？使用中有什么要注意的？",
     "防化手套的渗透时间（Breakthrough Time）是指化学品穿透手套材料到达内表面的时间。这是选择手套最重要的参数。使用注意：1) 渗透时间因化学品和手套材质而异，同一种手套对不同化学品渗透时间差异很大;2) 常见丁腈手套对丙酮渗透时间仅数分钟（需频繁更换）;3) 双层手套增加保护时间（内层和外层不同材质更佳）;4) 一旦感觉到手套内湿滑或有化学品气味，立即脱除更换;5) 脱除污染手套时应避免皮肤接触手套外表面（正确脱除方法：手套外表面不接触皮肤）。"),
    ("护目镜防雾处理", "眼部防护",
     "护目镜起雾了怎么办？可以佩戴时擦拭吗？",
     "护目镜起雾的正确处理：1) 不可在实验过程中取下护目镜擦拭;2) 使用前用防雾液或防雾湿巾预处理镜片;3) 紧急替代方案：用少量洗洁精轻涂镜片内表面并擦亮（可临时防雾）;4) 选择带防雾涂层的护目镜（较新设备普遍具备）;5) 佩戴前调整好鼻托和松紧带确保密封;6) 起雾严重时：走到安全区域（仍佩戴护目镜），再用干净纸巾擦拭;7) 请勿为防雾而在护目镜上开孔或降低密封性。"),
    ("防噪耳塞/耳罩", "听力防护",
     "实验室什么情况下需要戴耳塞？",
     "当实验室设备噪声超过85分贝（dBA）时需要听力防护。常见需要佩戴的场景：1) 超声波破碎仪/超声清洗器工作区域（高频噪声损伤听力）;2) 真空泵长时间运行区;3) 大型通风柜/排风系统机房;4) 粉碎机/研磨机操作;5) 气动工具使用。简单自检：站在设备旁1米处，需要提高嗓门才能跟人说话——说明噪声超过安全阈值，需要防护。佩戴方式：入耳式耳塞需捏细后塞入耳道并用手指顶住等回弹;耳罩式需确保密封良好。"),
    ("实验鞋选择", "鞋类防护",
     "实验室为什么不允许穿拖鞋和凉鞋？应该穿什么鞋？",
     "实验室鞋类要求是基础防护：实验室必须穿封闭式鞋子（鞋头和鞋面完全覆盖脚部）。禁止拖鞋、凉鞋、高跟鞋的原因：1) 化学品溅到脚上造成灼伤（裸足接触化学品伤害严重）;2) 碎玻璃/针头坠落刺伤;3) 重物掉落砸伤脚趾;4) 静电积累（某些鞋底材质）;5) 紧急撤离时扭伤/摔倒。推荐：皮面或合成革面的安全鞋最佳，至少应为全封闭运动鞋。帆布鞋不推荐（化学品可渗透）。"),
    ("围裙和防化服选择", "身体防护",
     "什么样的操作需要穿防化围裙或防化服？",
     "超过普通实验服防护能力时需要额外身体防护：1) 防化围裙（丁基橡胶或PVC材质）——处理大量酸/碱/强腐蚀品时穿在实验服外;2) 防化服——处理高毒/大量危险化学品或紧急泄漏处置时使用;3) 防化围裙选择要点：材质需与所处理的化学品兼容（查SDS）;4) 防化服分A/B/C/D级——实验室常用C级（化学防溅服+全面罩空气过滤呼吸器）;5) 使用完毕的防化围裙需清洗外表面（或作为危废处置一次性使用款）;6) 普通实验服湿了应立即更换（湿的织物渗透更快）。"),
]

# --- 通用安全制度和管理 ---
REGULATIONS = [
    ("实验室安全巡检制度", "安全制度",
     "实验室安全日常巡检应该检查哪些内容？",
     "实验室安全巡检（建议每周至少一次）检查清单：1) 化学品储存：有无过期/变质/无标签化学品;防火柜门是否关闭;2) 气瓶安全：气瓶是否固定;瓶帽是否盖好;有无漏气声;3) 通风柜：风速是否正常;前窗是否破损;内有无长期堆放;4) 消防器材：灭火器是否在有效期;消防通道是否畅通;安全出口指示灯是否亮;5) 应急设施：洗眼器/安全淋浴出水是否正常（每周放水测试一次）;6) 电气安全：电线和插座是否完好;有无私拉乱接;7) PPE：实验服/护目镜/手套是否充足;8) 废弃物：废液桶是否满溢;标签是否完整;9) 冰箱/冰柜：有无化学品泄漏;温度记录是否正常。"),
    ("实验室化学品的MSDS管理", "安全制度",
     "实验室必须拥有哪些化学品的MSDS？如何使用和存放？",
     "MSDS（化学品安全技术说明书）管理要求：1) 实验室使用的每一种危险化学品都必须在实验室内保留一份MSDS;2) MSDS应存放在化学品附近显眼位置或装订成册放在指定位置（如实验室入口）;3) 所有实验人员必须知道MSDS的位置并在使用新化学品前查阅;4) MSDS关键信息：危险性概述、急救措施、消防措施、泄漏应急处理、操作处置与储存、个体防护;5) 电子版MSDS备存（校内共享网盘或化学品管理系统）;6) MSDS应使用中文版（进口试剂可附带英文但中文版为必须）。"),
    ("实验记录的规范要求", "安全制度",
     "实验记录有哪些规范要求？为什么要做好实验记录？",
     "实验记录是实验室管理的基础，具有法律效力：1) 使用装订好的实验记录本（不得使用活页），页码连续;2) 用不可擦除的笔书写（签字笔/钢笔，不得用铅笔）;3) 记录内容：实验日期、目的、实验步骤、实际使用试剂（品名/批号/用量）、仪器参数、观察结果、数据、签名;4) 错误处划线标注（保留原始文字可读），在旁边修改并签名日期;5) 每页实验结束签名和日期;6) 电子实验记录系统需有审计追踪功能;7) 实验记录保存至少10年（涉及知识产权或安全的更长时间）。"),
    ("实验室安全检查整改闭环", "安全制度",
     "安全检查发现的问题如何确保整改到位？",
     "安全检查整改闭环流程：1) 检查人出具书面检查报告（问题描述/照片/风险等级/建议整改期限）;2) 实验室负责人签收并制定整改方案;3) 能现场立即整改的立即整改（如清理消防通道）;4) 需要经费或采购的列入计划，但需采取临时管控措施（如张贴警示标识）;5) 整改完成后拍照存档并通知检查人复查;6) 复查通过后关闭该问题;7) 建立整改台账（问题-责任人-整改-复查全链条可追溯）;8) 每月统计分析常见问题,针对性改进。"),
    ("高校实验室安全相关法律法规清单", "安全制度",
     "高校实验室安全管理需要遵守哪些主要法律法规？",
     "主要适用法规和标准：1) 《安全生产法》（2021修订）;2) 《危险化学品安全管理条例》（国务院令第591号）;3) 《易制毒化学品管理条例》;4) 《高等学校实验室安全规范》（教育部2024）;5) 《高等学校消防安全管理规定》（教育部令第28号）;6) GB 19489-2008《实验室生物安全通用要求》;7) GB 13690-2009《化学品分类和危险性公示通则》;8) GB/T 16483-2008《化学品安全技术说明书内容和项目顺序》;9) GB 18597《危险废物贮存污染控制标准》;10) GB/T 13869《用电安全导则》。各高校还应有本校的实验室安全管理制度汇编。"),
    ("化学实验室每日安全检查", "安全制度",
     "化学实验室每天下班前必须检查什么？",
     "化学实验室「每日关门前安全检查」清单：1) 所有加热设备（烘箱/马弗炉/加热搅拌器/水浴锅等）已关闭;2) 通风柜前窗已拉下;3) 所有气瓶阀门已关闭（确认无~嘶~漏气声）;4) 所有化学品瓶/试剂瓶已盖紧;5) 废液桶盖子已盖好;6) 冰箱/冷柜/低温设备运行正常;7) 门窗已锁闭;8) 水电无异常;9) 最后离开者在安全日志上签字。实行「最后离开检查制度」——物理或电子签到确保有人负责。"),
    ("生物实验室清洁消毒", "安全制度",
     "生物实验室应该如何进行日常清洁消毒？",
     "生物实验室清洁消毒要求：1) 实验台面每日实验后用70%乙醇或适当消毒剂擦拭;2) 每周至少一次全面清洁（包括地面湿拖——不可干扫）;3) 不同生物安全等级区域的清洁工具分开使用（颜色区分）;4) 消毒剂定期轮换（防止微生物产生抗性）——如交替使用70%乙醇、含氯消毒剂、季铵盐类;5) 使用含氯消毒剂时注意通风（释放氯气可能）;6) 清洁记录包括日期、区域、消毒剂种类、操作人。"),
    ("实验动物伦理与安全管理", "安全制度",
     "使用实验动物需要遵循什么规定？",
     "涉及实验动物的研究需遵循：1) 实验动物使用方案必须经实验动物伦理委员会审批（IACUC）方可开展;2) 遵循3R原则：替代(Replacement)、减少(Reduction)、优化(Refinement);3) 实验动物需在具有实验动物使用许可证的设施内饲养和使用;4) 动物咬伤/抓伤：立即流水冲洗、消毒、就医;5) 动物尸体/组织按生物危废处置（冷冻暂存、交无害化处理）;6) 接触实验动物的人员需进行相关人畜共患病风险评估和防护。"),
]

# --- 更多化学安全 ---
MORE_CHEM_SAFETY = [
    ("实验气体（氢气）安全使用", "气体安全",
     "使用氢气作为气相色谱载气或反应气体时需要注意什么？",
     "氢气是极易燃气体（爆炸极限4%-75%，极宽），使用要求严格：1) 氢气气瓶必须存放在室外气瓶间或专用氢气柜中，通过管道引入实验室;2) 氢气管道需明确标识（红色/黄色带）和定期检漏;3) 使用氢气的设备必须有氢气传感器和自动切断装置;4) 实验室顶部需有通风口（氢气比空气轻，积聚在天花板附近）;5) 禁止在氢气使用区使用明火或产生火花的操作;6) 每天下班前确认氢气气瓶阀门已关闭。FID检测器用氢气:使用完毕先关氢气再关空气。"),
    ("不锈钢高压反应釜安全", "压力容器",
     "使用不锈钢高压反应釜进行水热/溶剂热反应时有哪些安全要求？",
     "高压反应釜操作风险很高（压力爆炸）：1) 每次使用前检查密封圈/O圈是否完好和正确安装;2) 液体装填量不超过釜容积的60-70%（留足够膨胀空间）;3) 不同PTFE内衬和釜体型号对应不同的最高温度和压力——查阅手册，不可超限使用;4) 升温速率控制在5°C/min以内;5) 反应结束必须自然冷却至室温后（<40°C）方可开启;6) 反应釜置于防爆钢套中运行;7) 不可加热密闭的有机溶剂体系（压力急剧升高）;8) 定期检查釜体和螺纹有无腐蚀或裂纹。"),
    ("手套箱内操作安全", "惰性气氛",
     "在手套箱内进行无水无氧操作时需要注意什么？",
     "手套箱是进行空气/水敏感反应的专用设备：1) 进出手套箱的物品需经过过渡仓置换（至少3次真空-惰气循环）;2) 禁止将以下物品带入：水溶液（大量水蒸气毒化催化剂）、敞口挥发溶剂（破坏循环系统）、尖锐物品（可能刺破手套）;3) 手套箱内不存放大量溶剂和化学品（维持清洁）;4) 循环系统氧含量和水含量定期检查（H₂O/O₂<1ppm为正常）;5) 手套破损（哪怕针尖大小）需立即停止使用并更换;6) 使用后的针头、注射器妥善包裹后出仓（防止刺破手套）。"),
    ("氮气钢瓶使用安全", "气体安全",
     "使用氮气有什么安全注意事项？",
     "氮气虽不可燃，但因其窒息性，使用需注意：1) 氮气泄漏会置换空气中的氧气——无色无味，人在毫无察觉中昏迷;2) 使用氮气的实验室需通风良好，不可在密闭小间内大量使用;3) 使用可燃气体和氮气混合实验（如制备还原气氛）时，精确控制流量比;4) 液氮补充时在通风处操作;5) 进入曾大量使用氮气/氩气的密闭空间前，必须检测氧含量（携氧报警仪）;6) 氮气压力和减压阀规范——同其他气瓶安全要求。"),
]


def make_row(category: str, subcategory: str, lab_type: str,
             risk_level: str, hazard_types: str, scenario: str,
             title: str, question: str, answer: str, steps: str,
             ppe: str, forbidden: str, disposal: str,
             first_aid: str, emergency: str,
             source_title: str, source_org: str, source_url: str,
             tags: str) -> dict[str, Any]:
    return {
        "id": _next_id(),
        "title": title,
        "category": category,
        "subcategory": subcategory,
        "lab_type": lab_type,
        "risk_level": risk_level,
        "hazard_types": hazard_types,
        "scenario": scenario,
        "question": question,
        "answer": answer,
        "steps": steps,
        "ppe": ppe,
        "forbidden": forbidden,
        "disposal": disposal,
        "first_aid": first_aid,
        "emergency": emergency,
        "legal_notes": "",
        "references": "",
        "source_type": "regulatory_standard",
        "source_title": source_title,
        "source_org": source_org,
        "source_version": "",
        "source_date": "",
        "source_url": source_url,
        "last_updated": TODAY,
        "reviewer": "auto-generate; pending human review",
        "status": "draft",
        "tags": tags,
        "language": "zh-CN",
    }


def generate_chemical_entries() -> list[dict[str, Any]]:
    """每个化学品生成 3 个 Q&A 条目：储存、应急处置、安全使用"""
    rows = []
    default_src = ("高等学校实验室安全规范（教育部2024）", "教育部",
                   "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")

    for name, eng, hazards, risk, note in CHEMICALS:
        sn = name.split("/")[0]  # 简短名

        # 1）储存
        rows.append(make_row(
            category="化学", subcategory="危化品储存", lab_type="化学",
            risk_level=risk, hazard_types=hazards, scenario=f"{sn}的安全储存",
            title=f"危化品-{sn}储存",
            question=f"{sn}应该如何正确储存？",
            answer=f"{sn}（{eng}）属于{hazards}类化学品。储存要求：存放在阴凉、干燥、通风良好的化学品储存柜中，远离热源/明火/阳光直射。与不相容化学品隔离存放。瓶身贴有清晰标签（品名、浓度、危害标识、日期）。使用后立即盖紧瓶盖。{note}",
            steps=f"确认化学品柜类别;检查瓶身标签和密封;与不相容物分开存放;记录存放位置和数量",
            ppe="搬运时佩戴护目镜、实验服、防化手套",
            forbidden="禁止敞口存放;禁止与氧化剂/不相容试剂混放;禁止无标签存放;禁止在通风柜外长期存放",
            disposal=f"过期或废弃{sn}按危废分类处理",
            first_aid="皮肤接触：大量清水冲洗;眼睛接触：洗眼器冲洗并就医;吸入：移至通风处",
            emergency="大量泄漏：隔离区域，通风，用惰性吸收材料处理",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{sn};储存;MSDS;{eng}",
        ))

        # 2）应急处置（泄漏/暴露）
        rows.append(make_row(
            category="化学", subcategory="应急", lab_type="化学",
            risk_level=risk, hazard_types=hazards, scenario=f"{sn}泄漏或人员暴露",
            title=f"应急-{sn}应急处置",
            question=f"{sn}泄漏了或者溅到身上了怎么处理？",
            answer=f"{sn}（{eng}）应急处理：泄漏处理——小量泄漏用惰性吸收材料（如蛭石/硅藻土）覆盖并收集到危废袋中;大量泄漏隔离区域、通风、佩戴PPE后收集。人员暴露——皮肤接触：立即脱去污染衣物，用大量清水冲洗至少15分钟;眼睛接触：立即用洗眼器冲洗至少15分钟并就医;吸入：立即转移到通风处。{note}带上该化学品的SDS就医。",
            steps=f"泄漏：停止实验→隔离区域→通风→佩戴PPE→吸收/收集→危废处置;暴露：立即冲洗→脱去污染衣物→就医→报告",
            ppe="处理泄漏时：护目镜、防化手套、实验服、必要时面罩和呼吸防护",
            forbidden=f"禁止徒手处理泄漏;禁止将泄漏物冲入下水道;禁止使用易燃材料（如纸巾）吸附氧化性{sn}泄漏",
            disposal="泄漏吸收材料和污染PPE作为危废处置",
            first_aid=f"按{sn}的SDS急救指引处理;尽快就医",
            emergency=f"大量{sn}泄漏且超出自身处置能力：立即疏散并报告，拨打119",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{sn};应急;泄漏;暴露;{eng}",
        ))

        # 3）安全使用注意事项
        rows.append(make_row(
            category="化学", subcategory="危化品安全", lab_type="化学",
            risk_level=risk, hazard_types=hazards, scenario=f"{sn}的实验操作",
            title=f"危化品-{sn}安全操作",
            question=f"使用{sn}时需要佩戴什么PPE？有哪些禁止操作？",
            answer=f"操作{sn}（{eng}）的PPE和安全要求：必须佩戴护目镜、防化手套（查SDS确认手套材质适用性）和实验服。在有通风和工程控制（通风柜/局部排风）的条件下操作。{note}具体要求：1) 实验前查阅SDS了解危险性和急救措施;2) 在通风柜内操作（如适用）;3) 用后立即清洁外壁并盖紧瓶盖。",
            steps="查阅SDS;穿戴正确PPE;在通风柜内操作（如需要）;使用最小必要量;用后清洁密封;洗手",
            ppe="护目镜;防化手套（查SDS选择合适的材质）;实验服;封闭鞋",
            forbidden="禁止无PPE接触;禁止在通风柜外操作（挥发性/有毒品）;禁止敞口放置;禁止与不相容化学品靠近",
            disposal=f"含{sn}的废液/废物按相应危废类别处置",
            first_aid="按SDS指引处理暴露;就医时携带SDS",
            emergency="异常情况（泄漏/起火/暴露）：按应急预案处理",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{sn};PPE;安全操作;{eng}",
        ))
    return rows


def generate_equipment_entries() -> list[dict[str, Any]]:
    """每个设备生成 1 个 Q&A 条目"""
    rows = []
    default_src = ("高等学校实验室安全规范（教育部2024）", "教育部",
                   "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")
    for name, etype, hazards, risk, rule in EQUIPMENT:
        rows.append(make_row(
            category="设备安全", subcategory=etype, lab_type="通用",
            risk_level=risk, hazard_types=hazards, scenario=f"{name}的安全操作",
            title=f"设备-{name}安全使用",
            question=f"{name}的安全操作注意事项是什么？",
            answer=f"{name}是实验室{etype}。{rule}。主要风险：{hazards}。使用前必须阅读设备SOP并经过培训;使用中按规定佩戴PPE;使用后清洁并按规程关闭。",
            steps=f"阅读SOP;检查设备状态;佩戴PPE;按规程操作;使用后清洁关闭;记录",
            ppe="根据设备类型和操作风险选择相应PPE",
            forbidden="禁止未经培训独立操作;禁止绕过安全联锁装置;禁止在设备运行时离开",
            disposal="相关耗材和废物按规定处置",
            first_aid="根据伤害类型按应急预案处理",
            emergency="设备异常：立即按紧急停止，断电，报告管理人员",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{name};{etype};设备安全;SOP",
        ))
    return rows


def generate_scenario_entries(scenarios: list, cat: str, subcat: str) -> list[dict[str, Any]]:
    """通用场景条目生成"""
    rows = []
    default_src = ("高等学校实验室安全规范（教育部2024）", "教育部",
                   "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")
    for data in scenarios:
        if len(data) == 4:
            title, stype, question, answer = data
        else:
            continue
        rows.append(make_row(
            category=cat, subcategory=subcat, lab_type=cat,
            risk_level="4", hazard_types=stype, scenario=title,
            title=f"{subcat}-{title}",
            question=question,
            answer=answer,
            steps="按SOP和应急预案执行",
            ppe="根据具体场景选择合适的PPE",
            forbidden="禁止未经培训擅自处理;禁止无视安全警告",
            disposal="按相应危废/生物危废规定处置",
            first_aid="根据伤害类型执行对应急救措施",
            emergency="启动相应应急预案;报告管理人员;必要时拨打119/120",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{title};{stype};应急;安全",
        ))
    return rows


def generate_ppe_entries() -> list[dict[str, Any]]:
    """PPE 条目"""
    rows = []
    default_src = ("高等学校实验室安全规范（教育部2024）; OSHA 29 CFR 1910.132", "教育部 / OSHA",
                   "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")
    for title, stype, question, answer in PPE_SCENARIOS:
        rows.append(make_row(
            category="通用", subcategory="PPE", lab_type="通用",
            risk_level="2", hazard_types=stype, scenario=title,
            title=f"PPE-{title}",
            question=question,
            answer=answer,
            steps="按上述指引执行;如不确定请咨询实验室安全管理人员",
            ppe="参考答案中建议的PPE",
            forbidden="禁止在PPE失效/破损时继续操作;禁止共享个人PPE",
            disposal="一次性PPE使用后按相应类别（化学/生物/普通）废弃物处置",
            first_aid="",
            emergency="",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{title};PPE;{stype};个人防护",
        ))
    return rows


def generate_regulation_entries() -> list[dict[str, Any]]:
    """安全制度条目"""
    rows = []
    default_src = ("高等学校实验室安全规范（教育部2024）", "教育部",
                   "https://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html")
    for title, stype, question, answer in REGULATIONS:
        rows.append(make_row(
            category="通用", subcategory="安全制度", lab_type="通用",
            risk_level="1", hazard_types=stype, scenario=title,
            title=f"制度-{title}",
            question=question,
            answer=answer,
            steps="",
            ppe="",
            forbidden="",
            disposal="",
            first_aid="",
            emergency="",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{title};{stype};安全制度;管理",
        ))
    for title, stype, question, answer in MORE_CHEM_SAFETY:
        cat = "化学" if "化学" in stype or "气体" in stype or "压力" in stype or "惰性" in stype else "通用"
        rows.append(make_row(
            category=cat, subcategory=stype, lab_type=cat,
            risk_level="3", hazard_types=stype, scenario=title,
            title=f"安全-{title}",
            question=question,
            answer=answer,
            steps="按上述安全要求执行",
            ppe="根据操作类型选择PPE",
            forbidden="禁止违反上述安全要求",
            disposal="按相应类别危废处置",
            first_aid="",
            emergency="",
            source_title=default_src[0], source_org=default_src[1], source_url=default_src[2],
            tags=f"{title};{stype};安全",
        ))
    return rows


def main() -> int:
    all_new: list[dict[str, Any]] = []

    print("Generating chemical MSDS entries...")
    all_new.extend(generate_chemical_entries())
    print(f"  Chemicals: {len(all_new)} entries")

    before_eq = len(all_new)
    print("Generating equipment SOP entries...")
    all_new.extend(generate_equipment_entries())
    print(f"  Equipment: {len(all_new) - before_eq} entries")

    before_em = len(all_new)
    print("Generating emergency scenario entries...")
    all_new.extend(generate_scenario_entries(EMERGENCY_SCENARIOS, "通用", "应急"))
    all_new.extend(generate_scenario_entries(WASTE_SCENARIOS, "化学", "危废处置"))
    print(f"  Scenarios: {len(all_new) - before_em} entries")

    before_ppe = len(all_new)
    print("Generating PPE entries...")
    all_new.extend(generate_ppe_entries())
    print(f"  PPE: {len(all_new) - before_ppe} entries")

    before_reg = len(all_new)
    print("Generating regulation entries...")
    all_new.extend(generate_regulation_entries())
    print(f"  Regulations: {len(all_new) - before_reg} entries")

    print(f"\nTotal new entries generated: {len(all_new)}")

    # Load existing, deduplicate, merge
    existing: list[dict[str, str]] = []
    if KB_FILE.exists():
        with KB_FILE.open("r", encoding="utf-8-sig", newline="") as f:
            existing = list(csv.DictReader(f))
    print(f"Existing entries: {len(existing)}")

    existing_ids = {r.get("id", "") for r in existing}
    existing_sigs = set()
    for r in existing:
        sig = _sig(r.get("title", ""), r.get("question", ""))
        existing_sigs.add(sig)

    truly_new = []
    for r in all_new:
        if r["id"] in existing_ids:
            continue
        sig = _sig(r["title"], r["question"])
        if sig in existing_sigs:
            continue
        existing_sigs.add(sig)
        existing_ids.add(r["id"])
        truly_new.append(r)

    print(f"Truly new (after dedup): {len(truly_new)}")

    if not truly_new:
        print("No new entries to add.")
        return 0

    all_rows = existing + truly_new
    with KB_FILE.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=HEADERS)
        writer.writeheader()
        for row in all_rows:
            clean = {h: row.get(h, "") for h in HEADERS}
            writer.writerow(clean)

    print(f"Total after merge: {len(all_rows)}")
    print(f"Done. File: {KB_FILE}")

    # Stats
    cats: dict[str, int] = {}
    for r in all_rows:
        c = r.get("category", "unknown")
        cats[c] = cats.get(c, 0) + 1
    print("\nCategory distribution:")
    for c, n in sorted(cats.items(), key=lambda x: -x[1]):
        print(f"  {c}: {n}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
