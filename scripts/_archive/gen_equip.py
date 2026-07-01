import csv
import sys
from datetime import datetime

records = []

def add(title, category, question, answer, hazards, steps, org, url, risk):
    records.append({
        'title': title, 'category': category, 'question': question,
        'answer': answer, 'hazard_types': hazards, 'steps': steps,
        'source_org': org, 'source_url': url, 'risk_level': risk,
    })

# === 1. Autoclave (Stanford EHS) ===
add('高压灭菌器(Autoclave)安全操作规范', '设备',
    '高压灭菌器的安全操作要求有哪些？',
    '高压灭菌器操作存在物理危害（高温、蒸汽、压力）和生物危害。基本安全操作要求：1.操作前必须接受培训 2.不要对含有腐蚀性、溶剂、挥发性或放射性材料的物品灭菌 3.装载前检查灭菌腔内是否有遗留物品，确保排水滤网清洁，门密封圈完好 4.按制造商建议装载，切勿超载；玻璃器皿应放在耐热塑料托盘上 5.确保门完全关闭并锁紧，选择正确的灭菌循环 6.佩戴适当的PPE：耐热手套和臂套、橡胶围裙、护目镜、面罩 7.开门时缓慢操作，头脸手远离开口 8.卸载前让物品冷却至少10分钟 9.每次装载使用热敏指示胶带监测，每月使用生物指示剂验证 10.发现故障立即停用并张贴警示标识',
    '高温灼伤;蒸汽烫伤;压力爆炸;生物气溶胶;玻璃破裂',
    '操作前培训→检查设备状态→正确装载→选择循环→冷却后卸载→监测记录',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/autoclave-safety', '3')

add('高压灭菌器液体灭菌安全操作', '设备',
    '使用高压灭菌器对液体进行灭菌时需要注意什么？',
    '液体灭菌循环时间更长但温度较低，减压时间也更长，避免液体沸腾溢出。安全要点：1.装载前必须将液体容器的瓶盖拧松 2.仅使用硼硅酸盐玻璃（如Pyrex或Kimax） 3.使用带实心底部和壁的耐热托盘盛装内容物 4.液体应放在装有约1英寸水的耐热塑料托盘中 5.液体瓶不应超过2/3满，瓶间保持1-2英寸间距 6.卸载后让液体冷却至少1小时 7.处理热液体时必须佩戴面罩、护目镜和耐热手套',
    '高温液体喷溅;玻璃瓶破裂;蒸汽烫伤;压力伤害',
    '拧松瓶盖→使用耐热玻璃和托盘→控制装填量→保持间距→选择液体循环→充分冷却后卸载',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/autoclave-safety', '4')

add('高压灭菌器干热负载灭菌安全', '设备',
    '高压灭菌器对干热负载灭菌有哪些安全注意事项？',
    '干热负载灭菌安全要点：1.在托盘内加入1/4至1/2英寸的水，确保内容物均匀加热 2.检查塑料材料是否适合灭菌；聚乙烯塑料（LDPE和HDPE）不能灭菌 3.卸载后让材料冷却至少15分钟 4.不要超载，确保蒸汽能充分接触所有表面 5.使用热敏指示胶带监测每次装载 6.定期使用生物指示剂验证灭菌效果',
    '高温烫伤;塑料熔化;不均匀加热导致灭菌失败',
    '托盘加水→检查材料兼容性→正确装载→选择干热循环→冷却15分钟后卸载→监测记录',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/autoclave-safety', '3')

# === 2. Centrifuge (Stanford EHS) ===
add('离心机(Centrifuge)安全操作规范', '设备',
    '离心机的安全操作要求有哪些？',
    '离心机利用离心力分离物质。若使用或维护不当，所有离心机都可能产生危害。危害类型：物理危害（机械故障）、暴露危害（气溶胶化）。安全操作要求：1.建立定期维护计划 2.对高速和超速离心机记录运行日志 3.转子达到推荐寿命后退役 4.完成实验室特定的离心机培训 5.佩戴PPE：安全眼镜、手套、实验服、长裤和封闭式鞋 6.使用前检查试管、转子、安全杯、O型圈 7.离心生物危害材料时在生物安全柜中装载/卸载 8.使用密封试管和安全杯 9.平衡样品 10.启动后不离机，发现异常立即停止 11.完全停止后再开盖；危险材料离心后等待10分钟 12.检查是否有泄漏/溢出',
    '机械故障;金属碎片飞出;气溶胶暴露;样品泄漏;转子破裂',
    '培训→PPE→检查设备→准备样品→平衡装载→启动监控→停止后等待→检查泄漏→清洁维护',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/centrifuge-safety', '3')

add('离心机转子维护与更换', '设备',
    '离心机转子如何安全维护和更换？',
    '离心机转子维护要点：1.保持转子清洁干燥，防止腐蚀 2.使用后取出适配器并检查腐蚀情况 3.转子倒置存放在温暖干燥的地方 4.遵循手册关于清洁、检查、抛光、O型圈润滑的建议 5.使用后对接触过放射性或生物材料的转子进行去污 6.任何跌落或出现缺陷的转子立即停用 7.记录每个转子的使用日志 8.达到推荐寿命后退役 9.避免使用碱性清洁剂清洁铝制部件 10.避免使用研磨性钢丝刷清洁',
    '转子腐蚀;金属疲劳;转子破裂;结构缺陷',
    '日常清洁→定期检查→记录使用→到期退役→缺陷立即停用→制造商检查',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/centrifuge-safety', '3')

add('离心机生物危害材料泄漏应急处理', '设备',
    '离心机中生物危害材料发生泄漏时如何处理？',
    '离心机生物危害材料泄漏应急程序：1.立即关闭离心机 2.保持离心机盖关闭至少30分钟，让气溶胶沉降 3.穿戴PPE后打开离心机 4.检查样品、转子、安全杯和离心机井是否有泄漏 5.在生物安全柜中打开可密封的试管/安全杯/转子 6.使用镊子或钳子处理锋利碎片 7.用适当的消毒剂对离心机内部、转子和安全杯彻底消毒 8.按照生物危害废物处理程序处理受污染材料 9.记录事故并报告',
    '生物气溶胶;生物危害暴露;交叉感染;环境污染',
    '关闭离心机→等待30分钟→穿戴PPE→检查泄漏→生物安全柜中处理→消毒→废物处理→报告',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/reference/centrifuge-safety', '4')

# === 3. Cryogenic (Cornell EHS Chapter 16.10) ===
add('低温材料(液氮/液氦/干冰)安全操作规范', '设备',
    '实验室使用低温材料时有哪些安全要求？',
    '根据压缩气体协会定义，低温流体是指沸点低于-130F(-90C)的物质，包括液氮、氩、氦和固体二氧化碳(干冰)。主要危害：1.极端低温：可导致严重的冷接触烧伤，使塑料、橡胶、环氧树脂等材料变脆破裂 2.窒息：气化后体积膨胀约700:1，置换氧气造成缺氧危险。氧气浓度低于19.5%即视为缺氧环境，两口无氧空气即可使人失去意识 3.毒性：某些气体有毒，如一氧化碳、氟、一氧化二氮 4.易燃爆炸：可燃气体蒸发积聚可能导致火灾或爆炸。安全操作要求：1.佩戴宽松、厚重的皮革绝缘防护手套，袖子卷起并扣好 2.分配区域必须通风良好 3.避免在冷库、环境室等通风不良区域存放 4.必要时安装氧气监测仪/缺氧报警器 5.在密闭空间使用前必须进行危险评估 6.使用带压力释放装置的专用低温储存容器 7.避免将低温材料装入封闭系统 8.干冰在通风不良区域即使少量升华也可能超过5000ppm的允许暴露限值',
    '低温冻伤;冷接触烧伤;材料脆化破裂;窒息(缺氧);易燃爆炸',
    '危险评估→确保通风→佩戴绝缘手套和防护装备→使用专用容器→避免密闭空间→安装氧气监测→泄漏应急处理',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1610', '4')

add('液氮(Liquid Nitrogen)实验室安全使用', '设备',
    '实验室使用液氮时需要注意哪些安全事项？',
    '液氮沸点为-196C(-320F)，是实验室最常用的低温材料之一。安全使用要点：1.液氮接触温暖物体时会发生沸腾和飞溅，可能导致严重冻伤 2.塑料和橡胶等常见材料在低温下变脆并在应力下破裂 3.液氮从液体到气体的膨胀比约为700:1，在封闭系统中可产生巨大压力 4.分配区域必须通风良好，严禁在通风不良的空间中使用或存放 5.必须使用带压力释放系统的专用低温杜瓦瓶或储存容器 6.佩戴宽松、厚重的皮革绝缘手套，确保袖口扣好 7.使用护目镜或面罩防止飞溅 8.禁止将液氮密封在密闭容器中 9.运输时使用符合DOT要求的容器，总重量不超过220磅 10.在密闭空间使用前必须进行危险评估 11.液氮泄漏时立即撤离人员并加强通风 12.冻伤急救：用温水(40-42C)浸泡受冻部位，不要揉搓，立即就医',
    '极端低温冻伤;窒息(缺氧);压力爆炸;材料脆化;飞溅伤害',
    '检查容器完整性→确保通风→佩戴绝缘手套和护目镜→缓慢倾倒→避免密闭容器→泄漏时撤离→冻伤急救',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1610', '4')

add('液氦(Liquid Helium)实验室安全使用', '设备',
    '实验室使用液氦时有哪些特殊安全注意事项？',
    '液氦沸点极低(-269C/-452F)，是自然界中沸点最低的物质，主要用于核磁共振(NMR)等设备的超导磁体冷却。安全使用要点：1.液氦温度比液氮更低，冻伤风险更高，任何接触都可能导致立即和严重的组织损伤 2.液氦气化膨胀比约为700:1，窒息风险与液氮相同 3.必须在通风良好的区域使用，严禁在密闭空间存放 4.使用专用液氦杜瓦瓶，确保压力释放系统正常工作 5.佩戴多层绝缘低温手套（不能是普通防冻手套） 6.使用面罩或护目镜防止飞溅 7.液氦价格昂贵且供应有限，操作时应避免浪费 8.NMR磁体填充液氦时必须由经过培训的人员操作 9.磁体失超(quench)会瞬间释放大量氦气，必须确保房间通风系统能处理 10.失超可能导致磁体损坏和严重伤害，发现异常立即撤离 11.定期检查液氦液位，避免磁体因液氦不足而失超 12.运输液氦需符合DOT 2.2类危险品规定',
    '极端低温冻伤;组织瞬间冻结;窒息(缺氧);磁体失超;压力爆炸',
    '专业培训→检查杜瓦瓶和压力释放→确保通风→佩戴专用低温手套→缓慢操作→监控液位→失超时立即撤离',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/shipping-and-transportation/hazardous-materials-shipping-dot/cryogen-tips', '5')

# === 4. Biosafety Cabinet (Stanford EHS) ===
add('生物安全柜(BSC)安全使用规范', '设备',
    '生物安全柜的安全使用要求有哪些？',
    '生物安全柜（BSC）是为提供三种保护而设计的：1.保护人员免受柜内材料的伤害 2.保护柜内材料免受外部污染 3.保护环境免受柜内材料的污染。BSC分为三类：I类、II类和III类。Stanford不推荐使用I类BSC。安全使用要求：1.BSC必须安装在远离门和其他高流量区域的地方 2.BSC不应直接安装在另一台BSC或灭菌器的对面，建议至少相距6英尺 3.BSC不应直接安装在供气口下方 4.BSC不应安装在灭菌器10英尺范围内 5.BSC后方和两侧应提供12英寸的间隙 6.BSC内禁止使用明火 7.所有BSC必须提供适当的抗震固定装置 8.操作前让BSC运行至少5分钟 9.在柜内中央工作区域操作 10.尽量减少手臂进出柜子的次数 11.使用前后用适当的消毒剂清洁工作表面 12.定期由第三方供应商进行认证和再认证 13.移动BSC后必须由第三方供应商重新认证',
    '生物气溶胶暴露;交叉污染;气流失效;紫外线伤害;电气安全',
    '安装位置评估→启动预运行5分钟→消毒工作面→正确放置材料→中央区域操作→最小化手臂移动→使用后消毒→定期认证',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/biological-safety-cabinets-and-other-containment', '3')

add('生物安全柜(BSC)气流中断与泄漏应急处理', '设备',
    '生物安全柜发生气流中断或内部泄漏时如何处理？',
    '生物安全柜气流中断或泄漏应急程序：1.立即停止操作，将手臂从柜内撤出 2.不要关闭BSC（保持风机运行以维持负压） 3.如果发生生物危害材料泄漏：让BSC继续运行至少10分钟使气溶胶沉降；穿戴适当PPE；用适当的消毒剂从外向内擦拭泄漏区域；让消毒剂接触表面至少20-30分钟；用吸水材料吸收液体，作为生物危害废物处理 4.如果发生化学品泄漏：立即撤离并通知实验室主管 5.警报响起时：立即停止操作；检查窗口是否处于正确高度；如果警报持续，联系维修人员 6.紫外线灯使用：确保无人时开启；不要直视紫外线灯 7.记录所有事故并报告',
    '生物气溶胶泄漏;交叉污染;人员暴露;化学品暴露',
    '停止操作→保持风机运行→等待气溶胶沉降→穿戴PPE→消毒泄漏区域→废物处理→报告事故→维修验证',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/manual/laboratory-standard-design-guidelines/biological-safety-cabinets-and-other-containment', '4')

# === 5. Oven / Muffle Furnace (Cornell EHS Ch16.6 + OSHA) ===
add('实验室烘箱(Oven)安全使用规范', '设备',
    '实验室烘箱的安全使用要求有哪些？',
    '实验室烘箱用于干燥、加热和固化样品。常见危害包括火灾、烧伤和有毒气体释放。安全使用要求：1.仅用于预期用途，不得在烘箱中加热易燃或易爆材料 2.不要在烘箱中加热封闭容器，防止压力积聚导致爆炸 3.确保烘箱周围至少12英寸无易燃材料 4.不要在无人看管时运行烘箱 5.使用耐高温手套取出样品 6.定期清洁烘箱内部，清除溅出的化学品和残留物 7.检查烘箱温度控制器和报警系统是否正常工作 8.确保烘箱通风系统正常工作，防止有毒气体积聚 9.不要在烘箱顶部放置物品 10.发现异常气味、烟雾或温度失控立即关闭电源 11.使用防爆烘箱处理易燃溶剂（Class A烘箱） 12.每年由合格技术人员进行维护和校准',
    '火灾;高温灼伤;有毒气体释放;压力爆炸;电气故障',
    '检查温度控制器→清除易燃物→确保通风→正确装载→监控运行→使用耐热手套取出→定期清洁维护',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices', '3')

add('马弗炉(Muffle Furnace)高温安全操作', '设备',
    '使用马弗炉时有哪些高温安全注意事项？',
    '马弗炉可达到1000C以上高温，存在严重火灾和灼伤风险。安全操作要求：1.仅用于预期用途，不得加热易燃、易爆或挥发性材料 2.使用耐高温陶瓷或金属坩埚，不要使用普通玻璃器皿 3.确保炉门密封良好，但不要锁死（防止压力积聚） 4.佩戴耐高温手套、护目镜和防护服 5.使用长柄钳或坩埚钳取出样品，避免直接接触高温区域 6.确保炉体周围有足够通风，散热空间至少12英寸 7.不要在无人看管时运行马弗炉 8.加热过程中不要打开炉门，防止热冲击和灼伤 9.冷却至室温后再清理炉膛 10.定期检查加热元件和热电偶 11.确保紧急切断开关易于触及 12.在炉旁张贴高温警示标识',
    '高温灼伤;火灾;热辐射;电气故障;坩埚破裂',
    '检查设备和坩埚→确保通风→佩戴PPE→正确装载→关闭炉门→监控温度→冷却后取出→定期维护',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices', '4')

# === 6. Water Bath / Oil Bath / Sand Bath (Cornell EHS + general lab safety) ===
add('实验室水浴锅(Water Bath)安全使用', '设备',
    '实验室水浴锅的安全使用要求有哪些？',
    '水浴锅用于在精确温度下加热样品。安全使用要求：1.确保水浴锅放置在稳固、水平的表面上，远离易燃材料 2.使用蒸馏水或去离子水，防止水垢积聚 3.水位不应超过最高标记线，防止水溢出导致电气短路 4.定期检查并补充水位，防止干烧 5.不要在水浴锅中加热封闭容器 6.使用适当的容器支架，防止试管漂浮或倾倒 7.佩戴耐热手套取出样品 8.不要在无人看管时长时间运行 9.定期清洁水浴锅，防止细菌和藻类滋生 10.发现电气故障（如漏电、异味）立即停用并联系维修 11.水浴锅不应与电源插座共用高功率设备 12.使用后关闭电源并排空积水',
    '电气短路;烫伤;干烧;细菌污染;水溢出',
    '检查水位和水质→确保稳固放置→正确装载样品→监控温度→佩戴手套取出→定期清洁→使用后排空',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices', '2')

add('实验室油浴锅(Oil Bath)安全操作', '设备',
    '使用油浴锅加热时有哪些安全注意事项？',
    '油浴锅使用导热油在高于水沸点的温度下加热样品。存在火灾和灼伤风险。安全操作要求：1.仅使用适合高温的导热油（如硅油、矿物油），不要使用食用油或易燃液体 2.确保油浴锅配备温度控制器和过温保护装置 3.定期检查油的质量，发现变色、变稠或有异味时更换 4.油位不应超过最高标记线 5.不要在无人看管时运行油浴锅 6.佩戴耐热手套和护目镜 7.确保周围无易燃材料，油浴锅与易燃物保持至少12英寸距离 8.使用适当的容器支架 9.如果发现油冒烟或起火，立即关闭电源并使用干粉灭火器或金属盖子灭火（切勿用水） 10.定期清洁油浴锅外部，防止油渍积聚 11.废油按照危险废物处理程序处置 12.在油浴锅旁张贴高温和火灾风险警示',
    '火灾;高温灼伤;油溅伤;有毒油烟;电气故障',
    '检查油质和油位→确保周围无易燃物→佩戴PPE→正确装载→监控温度→紧急灭火准备→定期换油和清洁',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices', '4')

add('实验室沙浴(Sand Bath)安全使用', '设备',
    '使用沙浴加热时需要注意哪些安全事项？',
    '沙浴使用热沙作为传热介质，可均匀加热样品至高温。安全使用要求：1.仅使用干燥、清洁的沙子，不得含有有机物或易燃杂质 2.确保沙浴配备温度控制器 3.不要在无人看管时运行沙浴 4.佩戴耐热手套和护目镜，沙子可能飞溅 5.确保周围无易燃材料 6.使用耐热容器（如金属或陶瓷），不要使用普通玻璃 7.定期更换沙子，清除碳化和污染物 8.发现沙子冒烟或有异味立即关闭电源 9.冷却后清理溢出的沙子 10.不要将水或其他液体直接倒入热沙中，防止蒸汽爆炸',
    '高温灼伤;火灾;沙粒飞溅;蒸汽爆炸;电气故障',
    '检查沙子质量→确保周围无易燃物→佩戴PPE→正确装载→监控温度→定期更换沙子→冷却后清理',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/166-heat-and-heating-devices', '3')

# === 7. Vacuum Pump (Cornell EHS Ch16.12 + general) ===
add('实验室真空泵(Vacuum Pump)安全操作', '设备',
    '实验室真空泵的安全使用要求有哪些？',
    '真空泵用于产生负压，广泛应用于蒸馏、过滤和干燥等操作。安全使用要求：1.使用适合应用的泵类型（如旋转叶片泵、隔膜泵、涡旋泵） 2.确保泵的排气通风良好，防止有害气体积聚 3.使用冷阱防止溶剂蒸气进入泵油，延长泵寿命并减少火灾风险 4.定期检查泵油水平和质量，发现变色或污染时更换 5.不要泵送腐蚀性或颗粒状物质，除非使用专用泵 6.确保所有连接密封良好，防止泄漏 7.佩戴适当的PPE，特别是处理危险材料时 8.在泵的进气口安装适当的过滤器或捕集器 9.确保泵配备适当的压力释放装置 10.定期进行预防性维护 11.废泵油按照危险废物处理程序处置 12.发现异常噪音、振动或温度升高立即停用并检查',
    '有害气体暴露;泵油火灾;压力爆炸;电气故障;噪音伤害',
    '选择正确泵型→确保通风→安装冷阱→检查泵油→确保密封→佩戴PPE→定期维护→正确处理废油',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1612-glass-under-vacuum', '3')

add('真空玻璃器皿操作安全', '设备',
    '使用真空玻璃器皿时有哪些安全注意事项？',
    '真空玻璃器皿在负压下可能发生内爆，产生锋利的玻璃碎片。安全操作要求：1.仅使用专门设计的真空玻璃器皿（如厚壁烧瓶、抽滤瓶），不要使用普通玻璃器皿 2.使用前仔细检查玻璃器皿是否有裂纹、划痕或缺口 3.在真空容器外包裹防护网或胶带，防止内爆时碎片飞溅 4.使用防护屏或挡板保护操作者 5.确保所有连接牢固，使用适当的夹具固定 6.缓慢抽真空，避免压力急剧变化 7.释放真空时也要缓慢进行 8.佩戴安全眼镜和厚手套 9.不要在真空容器上方或前方放置面部 10.发现玻璃器皿损坏立即更换 11.使用防爆膜或安全阀防止过真空 12.在通风橱中操作涉及危险材料的真空系统',
    '玻璃内爆;碎片飞溅;割伤;压力伤害;化学品暴露',
    '检查玻璃器皿→包裹防护网→固定连接→缓慢抽真空→佩戴PPE→通风橱中操作→缓慢释放真空→损坏立即更换',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/1612-glass-under-vacuum', '4')

# === 8. Rotary Evaporator (NCBI Prudent Practices + general) ===
add('旋转蒸发仪(Rotary Evaporator)安全操作', '设备',
    '旋转蒸发仪的安全使用要求有哪些？',
    '旋转蒸发仪用于在减压下温和蒸发溶剂。存在火灾、爆炸和化学暴露风险。安全操作要求：1.确保设备安装在通风橱中或连接适当的排气系统 2.使用防爆型旋转蒸发仪处理易燃溶剂 3.检查所有玻璃连接和密封件是否完好 4.确保冷凝水循环系统正常工作 5.不要蒸发易爆、过氧化物形成或高反应性化学品 6.控制水浴温度，不要超过溶剂的闪点 7.使用适当的接收瓶，确保其能承受真空 8.佩戴安全眼镜和适当的防护手套 9.不要在无人看管时运行设备 10.定期检查真空泵油，及时更换受污染的泵油 11.确保紧急停止按钮易于触及 12.按照制造商规程进行维护和清洁',
    '火灾;溶剂蒸气暴露;爆炸;玻璃破裂;压力伤害',
    '确保通风→检查玻璃连接→设置合适温度→监控运行→佩戴PPE→定期维护泵和密封→正确处理废溶剂',
    'National Academies Press / NCBI Bookshelf',
    'https://www.ncbi.nlm.nih.gov/books/NBK55872/', '4')

# === 9. Freeze Dryer (general + manufacturer guidelines) ===
add('冷冻干燥机(Freeze Dryer/Lyophilizer)安全操作', '设备',
    '冷冻干燥机的安全使用要求有哪些？',
    '冷冻干燥机用于通过升华去除样品中的水分。涉及低温、高压和潜在生物危害。安全操作要求：1.确保设备放置在通风良好的区域 2.使用适合冷冻干燥的容器，确保其能承受低温和真空 3.正确安装冷凝器，确保制冷系统正常工作 4.在处理生物危害材料时使用适当的密封和 containment 装置 5.佩戴低温手套和护目镜，防止冷灼伤和飞溅 6.确保真空泵排气通风良好，防止有害气体积聚 7.定期检查真空密封和O型圈 8.不要在无人看管时运行设备 9.按照制造商规程进行除霜和清洁 10.废泵油按照危险废物处理程序处置 11.确保紧急停止装置易于触及 12.定期进行预防性维护',
    '低温冻伤;真空伤害;有害气体暴露;生物危害;电气故障',
    '确保通风→检查制冷系统→正确装载→密封生物危害样品→佩戴低温手套→监控运行→定期除霜和清洁→正确处理废油',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/manual/biosafety-manual/autoclaves', '3')

# === 10. Ultrasonic Cleaner (general lab safety) ===
add('超声波清洗器(Ultrasonic Cleaner)安全使用', '设备',
    '超声波清洗器的安全使用要求有哪些？',
    '超声波清洗器利用高频声波在液体中产生空化效应来清洁物品。存在噪音、电气和化学危害。安全使用要求：1.确保清洗器放置在稳固、水平的表面上 2.使用适当的清洗液，不得使用易燃或腐蚀性过强的液体 3.不要超过最高液位线 4.不要将手伸入运行中的清洗槽中，空化效应可能导致组织损伤 5.佩戴听力保护装置，长时间暴露于高频噪音可能导致听力损伤 6.确保设备接地良好，防止电气漏电 7.不要在无人看管时长时间运行 8.定期检查换能器和加热元件（如有） 9.发现异常噪音、振动或温度升高立即停用 10.更换清洗液时佩戴适当的手套和护目镜 11.确保清洗器盖子在运行时关闭，减少噪音和溅洒 12.按照制造商规程进行维护和清洁',
    '噪音伤害;组织损伤;电气漏电;化学暴露;液体溅洒',
    '选择适当清洗液→确保稳固放置→检查液位→佩戴听力保护→关闭盖子运行→不将手伸入→定期更换清洗液→定期维护',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards', '2')

# === 11. Incubator (Stanford EHS Biosafety Manual) ===
add('实验室培养箱(Incubator)安全使用', '设备',
    '实验室培养箱的安全使用要求有哪些？',
    '培养箱用于在受控温度、湿度和气体环境下培养细胞或微生物。安全使用要求：1.确保培养箱放置在通风良好、远离热源和阳光直射的位置 2.定期清洁和消毒内部表面，防止交叉污染 3.不要在培养箱中存放易燃、腐蚀性或挥发性化学品 4.确保温度和湿度传感器校准准确 5.使用适当的容器和托盘，防止泄漏 6.定期检查门密封圈，确保其完好无损 7.CO2培养箱应定期检查CO2浓度和供应 8.佩戴手套和实验服处理培养物 9.发现霉菌或细菌污染立即清洁和消毒 10.不要在无人看管时长时间运行高温程序 11.确保水盘使用无菌蒸馏水并定期更换 12.按照制造商规程进行维护和校准',
    '交叉污染;霉菌滋生;高温灼伤;CO2泄漏;电气故障',
    '确保通风和位置→定期清洁消毒→使用无菌水→检查密封→校准传感器→佩戴手套处理→定期维护',
    'Stanford University Environmental Health & Safety',
    'https://ehs.stanford.edu/manual/biosafety-manual/autoclaves', '2')

# === 12. Laboratory Refrigerator/Freezer (Cornell EHS + Stanford) ===
add('实验室冰箱/冰柜(Refrigerator/Freezer)安全使用', '设备',
    '实验室冰箱和冰柜的安全使用要求有哪些？',
    '实验室冰箱和冰柜用于储存化学品、样品和生物材料。存在火灾、爆炸和化学品泄漏风险。安全使用要求：1.仅使用专为实验室设计的冰箱/冰柜（防爆型或无火花型）储存易燃材料，家用冰箱严禁储存易燃品 2.所有容器必须密封良好并贴有清晰标签 3.不要在冰箱中存放开放容器或挥发性化学品 4.定期除霜和清洁，防止冰积聚和交叉污染 5.确保温度报警系统正常工作 6.不要将冰箱塞得过满，确保空气流通 7.易燃材料冰箱不得存放食品或饮料 8.定期检查门密封圈 9.发现异常温度波动、噪音或泄漏立即报告 10.制定并遵守样品清单和定期清理制度 11.确保紧急情况下可以快速切断电源 12.超低温冰箱(-80C)需要特殊培训才能操作',
    '火灾;爆炸;化学品泄漏;交叉污染;冻伤',
    '使用防爆冰箱→密封并标签所有容器→定期除霜清洁→监控温度→不存放食品→定期清理→紧急切断电源',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards', '3')

add('超低温冰箱(-80C)安全操作', '设备',
    '使用超低温冰箱(-80C)时有哪些特殊安全注意事项？',
    '超低温冰箱用于长期保存生物样品，温度可达-80C。存在冻伤、窒息和设备故障风险。安全操作要求：1.必须经过专门培训才能操作超低温冰箱 2.佩戴专用的低温手套、护目镜和防护服 3.打开冰箱门时动作要快，减少冷气流失和压缩机负荷 4.不要在冰箱中存放易燃、易爆或挥发性材料 5.确保冰箱周围通风良好，便于散热 6.定期检查温度记录和报警系统 7.制定样品清单，避免频繁开门寻找样品 8.确保备用电源或液氮备份系统正常工作 9.冰箱故障时立即转移样品到备用设备 10.定期进行预防性维护，包括清洁冷凝器和检查制冷剂 11.在冰箱旁张贴低温警示标识 12.确保紧急联系人信息随时可用',
    '极端低温冻伤;窒息(氮气泄漏);设备故障导致样品损失;电气故障;制冷剂泄漏',
    '培训→佩戴低温手套→快速存取→定期检查温度和报警→维护备用系统→定期预防性维护→紧急转移计划',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards', '4')

# === 13. Microscope (general lab safety) ===
add('实验室显微镜(Microscope)安全使用', '设备',
    '实验室显微镜的安全使用要求有哪些？',
    '显微镜是实验室常用光学设备，虽然风险较低，但仍需注意电气和人体工程学安全。安全使用要求：1.确保显微镜放置在稳固、水平的表面上，远离振动源 2.检查电源线和插头是否完好，确保接地良好 3.使用适当的照明强度，避免眼睛疲劳 4.调整目镜和物镜时动作轻柔，防止碰撞损坏 5.使用油镜时，仅使用指定的显微镜浸油，避免使用其他油品 6.使用后关闭光源，延长灯泡寿命并减少火灾风险 7.定期清洁光学部件，使用专用镜头纸和清洁液 8.确保良好的工作环境照明，减少眼睛疲劳 9.调整座椅和工作台高度，保持正确的人体工程学姿势 10.长时间观察时定期休息眼睛 11.处理生物危害样品时在生物安全柜中操作 12.按照制造商规程进行维护和校准',
    '眼睛疲劳;电气故障;人体工程学损伤;油镜污染;火灾(灯泡过热)',
    '确保稳固放置→检查电源→调整照明→轻柔操作→使用指定浸油→保持正确姿势→定期休息→清洁维护',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards', '1')

# === 14. LC-MS (Agilent + general) ===
add('液相色谱-质谱联用仪(LC-MS)安全操作', '设备',
    'LC-MS的安全使用要求有哪些？',
    'LC-MS结合了液相色谱的分离能力和质谱的检测能力，涉及高压、高温、真空和潜在有毒溶剂。安全操作要求：1.确保所有高压连接和管路密封良好，防止泄漏 2.使用适当的溶剂储存和废液收集系统，防止挥发和泄漏 3.确保质谱仪的真空泵排气通风良好或连接废气处理系统 4.处理有毒或腐蚀性流动相时佩戴适当的PPE 5.定期检查和更换离子源、喷雾针和毛细管 6.确保质谱仪的电气接地良好 7.不要在质谱仪运行时打开真空腔 8.使用氮气发生器或钢瓶时，确保气体供应系统安全 9.定期校准质量轴和检测器灵敏度 10.确保紧急停止按钮易于触及 11.废溶剂按照危险废物处理程序处置 12.按照制造商规程进行日常维护和清洁',
    '高压溶剂泄漏;有毒溶剂暴露;真空伤害;电气故障;高温灼伤',
    '检查连接密封→确保通风→佩戴PPE→监控溶剂液位→定期维护离子源→正确处置废溶剂→紧急停止装置检查',
    'Agilent Technologies',
    'https://www.agilent.com/en/product/liquid-chromatography/mass-spectrometry-lc-ms', '3')

# === 15. Pressure Vessel / Gas Cylinder (Cornell EHS Ch16.4 + OSHA) ===
add('实验室压力容器与气瓶安全使用', '设备',
    '实验室压力容器和气瓶的安全使用要求有哪些？',
    '压力容器和气瓶在高压下储存气体，存在爆炸、泄漏和窒息等严重风险。安全使用要求：1.所有气瓶必须直立固定，使用链条或支架防止倾倒 2.气瓶阀门保护盖在不使用时应始终安装 3.使用适当的调节器和管路，确保额定压力匹配 4.在连接调节器前缓慢打开阀门吹扫接口 5.使用肥皂水检查所有连接是否泄漏，严禁使用明火检漏 6.气瓶应储存在通风良好、远离热源和阳光直射的区域 7.易燃气体和氧化剂气瓶必须分开储存至少20英尺或用防火墙隔开 8.空瓶和满瓶应分开存放并明确标识 9.不要尝试修理或改装气瓶阀门 10.运输气瓶时必须使用手推车并固定 11.实验室中的气瓶数量应保持在最低必要水平 12.定期检查气瓶外观，发现凹陷、腐蚀或损坏立即报告供应商',
    '气瓶爆炸;气体泄漏;窒息;火灾;化学暴露',
    '直立固定→安装保护盖→检查调节器→缓慢开启→检漏→通风储存→分开存放易燃和氧化剂→正确运输→定期检查',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164-compressed-gases', '4')

add('乙炔气瓶特殊安全要求', '设备',
    '使用乙炔气瓶时有哪些特殊安全注意事项？',
    '乙炔是一种极不稳定、易燃易爆的气体，即使在无空气条件下也可能分解爆炸。特殊安全要求：1.乙炔气瓶必须始终直立存放和使用，严禁横放或倒置 2.储存温度不得超过52C(125F)，远离热源和明火 3.使用专用的乙炔调节器，不得使用其他气体调节器 4.乙炔气瓶与氧气气瓶必须分开至少20英尺或用防火墙隔开 5.使用回火防止器防止火焰回传至气瓶 6.确保所有连接使用左旋螺纹（与其他气体不同） 7.不要在乙炔管路上使用铜或银含量超过70%的合金配件 8.气瓶内压力低于25psi时停止使用并更换 9.在通风良好的区域使用，防止气体积聚 10.发现泄漏立即关闭阀门并撤离人员 11.乙炔气瓶空瓶也应作为危险品处理 12.储存区域张贴易燃气体警示标识',
    '爆炸;火灾;回火;分解反应;气体泄漏',
    '始终直立→远离热源→使用专用调节器→与氧气分开→安装回火防止器→使用左旋螺纹→避免铜配件→低压力时更换→通风使用',
    'Cornell University Environment, Health and Safety',
    'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164-compressed-gases', '5')

# === Import to knowledge base ===
import csv
from datetime import datetime

with open('knowledge_base_curated.csv', 'r', encoding='utf-8-sig', newline='') as f:
    kb_rows = list(csv.DictReader(f))

existing_titles = set(r['title'].strip() for r in kb_rows if r.get('title'))

max_num = 0
for r in kb_rows:
    rid = r.get('id','')
    if rid.startswith('KB-EQUIP2-'):
        try:
            num = int(rid.replace('KB-EQUIP2-',''))
            max_num = max(max_num, num)
        except:
            pass

print(f'Existing KB rows: {len(kb_rows)}')
print(f'Existing max KB-EQUIP2 num: {max_num}')

new_rows = []
skipped = 0
for rec in records:
    if rec['title'] in existing_titles:
        skipped += 1
        continue
    max_num += 1
    new_id = f'KB-EQUIP2-{max_num:04d}'
    new_rows.append({
        'id': new_id,
        'title': rec['title'],
        'category': rec['category'],
        'subcategory': '',
        'lab_type': '通用',
        'risk_level': rec['risk_level'],
        'hazard_types': rec['hazard_types'],
        'scenario': '',
        'question': rec['question'],
        'answer': rec['answer'],
        'steps': rec['steps'],
        'ppe': '',
        'forbidden': '',
        'disposal': '',
        'first_aid': '',
        'emergency': '',
        'legal_notes': '',
        'references': '',
        'source_type': 'authoritative_manual',
        'source_title': '',
        'source_org': rec['source_org'],
        'source_version': '',
        'source_date': '',
        'source_url': rec['source_url'],
        'last_updated': datetime.now().isoformat()[:10],
        'reviewer': 'auto-ingest-equip2; pending human review',
        'status': 'draft',
        'tags': f'equip2_batch;{rec["category"]}',
        'language': 'zh-CN',
        'suspension_reason': '',
        'suspension_date': '',
    })

print(f'Generated records: {len(records)}')
print(f'Duplicates skipped: {skipped}')
print(f'Records to import: {len(new_rows)}')

if new_rows:
    with open('knowledge_base_curated.csv', 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_rows[0].keys())
        writer.writerows(new_rows)
    print(f'Successfully imported {len(new_rows)} records')
else:
    print('No new records to import')

