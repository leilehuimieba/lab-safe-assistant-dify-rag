import csv
from datetime import datetime

CHEMICALS = [
    ('硫酸(Sulfuric Acid)', '强酸腐蚀;放热反应;化学灼伤;吸入危害', '佩戴PPE→在通风橱中操作→缓慢将酸加入水中(切勿反向)→使用耐酸容器→准备中和剂→泄漏时用碱中和后清理', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/SLTC/sulfuricacid/', '4'),
    ('盐酸(Hydrochloric Acid)', '强酸腐蚀;氯化氢气体;呼吸道刺激;化学灼伤', '佩戴PPE→在通风橱中操作→使用耐酸容器→避免与氧化剂接触→泄漏时用碱中和→气体泄漏时撤离并通风', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/192', '3'),
    ('硝酸(Nitric Acid)', '强氧化性;强酸腐蚀;氮氧化物气体;爆炸风险', '佩戴PPE→在通风橱中操作→远离有机物和还原剂→使用棕色瓶避光储存→泄漏时用碱中和→避免与金属粉末接触', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/386', '4'),
    ('氢氟酸(Hydrofluoric Acid)', '极强腐蚀性;氟离子中毒;可穿透皮肤破坏骨骼;致命风险', '必须在通风橱中操作→佩戴专用HF防护手套→佩戴面罩和围裙→现场备有葡萄糖酸钙凝胶→皮肤接触后立即用大量水冲洗并涂抹葡萄糖酸钙→立即就医', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/196', '5'),
    ('高氯酸(Perchloric Acid)', '强氧化剂;爆炸风险;强酸腐蚀', '必须使用专用高氯酸通风橱→远离有机物和还原剂→不要蒸发至干→储存于耐酸容器→泄漏时用大量水稀释→接触后立即冲洗就医', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/443', '5'),
    ('氢氧化钠(Sodium Hydroxide)', '强碱腐蚀;放热溶解;皮肤灼伤;眼睛损伤', '佩戴PPE→缓慢加入水中(切勿反向)→使用耐碱容器→避免与酸接触→泄漏时用酸中和后清理→皮肤接触后用大量水冲洗15分钟', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/528', '3'),
    ('氢氧化钾(Potassium Hydroxide)', '强碱腐蚀;放热溶解;皮肤灼伤;眼睛损伤', '佩戴PPE→缓慢加入水中→使用耐碱容器→避免与酸接触→泄漏时用酸中和→皮肤接触后立即冲洗', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/446', '3'),
    ('氨水(Ammonium Hydroxide)', '刺激性气体;呼吸道刺激;皮肤灼伤;眼睛损伤', '在通风橱中操作→佩戴PPE→远离卤素和氧化剂→密封储存→泄漏时加强通风→吸入后转移到新鲜空气处', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/33', '3'),
    ('甲醇(Methanol)', '易燃;有毒;可致盲;吸入危害', '远离火源和热源→在通风橱中操作→佩戴PPE→使用防爆设备→泄漏时加强通风→禁止饮用→吸入后转移到新鲜空气处→误服后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0397.html', '4'),
    ('乙醇(Ethanol)', '易燃;吸入危害;中枢神经系统抑制', '远离火源→在通风橱中操作→佩戴PPE→使用防爆设备→储存于防火柜→大量泄漏时撤离并通风→远离氧化剂', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0262.html', '2'),
    ('丙酮(Acetone)', '极易燃;挥发性强;皮肤脱脂;中枢神经系统抑制', '远离火源和热源→在通风橱中操作→佩戴PPE→使用防爆设备→储存于防火柜→禁止在丙酮附近使用明火→大量泄漏时撤离', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0004.html', '3'),
    ('乙醚(Diethyl Ether)', '极易燃;极易形成过氧化物;爆炸风险;麻醉作用', '远离火源→在通风橱中操作→佩戴PPE→使用防爆设备→储存于防火柜→定期检查过氧化物→发现过氧化物立即处理→禁止蒸干', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0277.html', '5'),
    ('乙酸乙酯(Ethyl Acetate)', '易燃;刺激性;中枢神经系统抑制', '远离火源→在通风橱中操作→佩戴PPE→储存于防火柜→大量泄漏时加强通风→避免与强氧化剂接触', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0267.html', '3'),
    ('正己烷(n-Hexane)', '易燃;神经毒性;慢性中毒;周围神经病变', '远离火源→在通风橱中操作→佩戴PPE→避免皮肤长期接触→储存于防火柜→定期健康检查→出现麻木或刺痛立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0312.html', '4'),
    ('甲苯(Toluene)', '易燃;神经毒性;生殖毒性;吸入危害', '远离火源→在通风橱中操作→佩戴PPE→避免孕妇接触→储存于防火柜→大量泄漏时撤离→出现头晕或恶心立即转移到新鲜空气处', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0619.html', '3'),
    ('二甲苯(Xylene)', '易燃;神经毒性;皮肤刺激;吸入危害', '远离火源→在通风橱中操作→佩戴PPE→避免皮肤长期接触→储存于防火柜→大量泄漏时撤离', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0667.html', '3'),
    ('二氯甲烷(Dichloromethane)', '致癌物;麻醉作用;心脏毒性;吸入危害', '必须在通风橱中操作→佩戴PPE→远离火源→禁止在明火附近使用→储存于防火柜→大量泄漏时撤离→暴露后立即就医', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/168', '4'),
    ('氯仿(Chloroform)', '致癌物;肝毒性;麻醉作用;吸入危害', '必须在通风橱中操作→佩戴PPE→远离火源→储存于防火柜→禁止长期接触→大量泄漏时撤离', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0107.html', '4'),
    ('甲醛(Formaldehyde)', '致癌物;呼吸道刺激;皮肤致敏;眼睛损伤', '必须在通风橱中操作→佩戴PPE(包括防甲醛手套)→避免皮肤和眼睛接触→密封储存→泄漏时加强通风→长期暴露需医学监测', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/formaldehyde', '4'),
    ('苯酚(Phenol)', '剧毒;皮肤吸收;组织坏死;全身中毒', '佩戴专用防护手套→在通风橱中操作→避免皮肤接触→立即冲洗接触部位→储存于耐腐蚀容器→泄漏时用沙土覆盖后收集', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0493.html', '4'),
    ('过氧化氢(Hydrogen Peroxide)', '强氧化剂;腐蚀性;分解爆炸;皮肤灼伤', '佩戴PPE→远离有机物和还原剂→避光储存于阴凉处→使用耐腐蚀容器→高浓度时远离火源→泄漏时用大量水稀释→皮肤接触后立即冲洗', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0335.html', '3'),
    ('氰化钾/氰化钠(Cyanide Salts)', '剧毒;可致命;可经皮肤吸收;快速作用', '必须在通风橱中操作→佩戴专用防护装备→现场备有解毒剂→严禁单独操作→泄漏时立即撤离→接触后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/idlh/cyanides.html', '5'),
    ('汞(Mercury)', '剧毒;蒸气吸入;神经系统损害;生物累积', '必须在通风橱中操作→佩戴专用防护装备→使用密闭系统→泄漏时用硫粉或专用汞吸附剂收集→严禁使用真空吸尘器→暴露后立即就医', 'U.S. Environmental Protection Agency', 'https://www.epa.gov/mercury/what-do-if-you-spill-more-mercury-amount-thermometer', '4'),
    ('铬酸(Chromic Acid)', '致癌物;强氧化剂;强腐蚀性;组织破坏', '必须在通风橱中操作→佩戴全面罩和专用手套→远离有机物和还原剂→使用耐腐蚀容器→泄漏时用大量水稀释→皮肤接触后立即冲洗15分钟', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/116', '4'),
    ('氢气(Hydrogen)', '极易燃;爆炸性混合物;无色无味;上升扩散', '远离火源和热源→使用防爆设备→通风良好→储存于专用气瓶柜→检漏→禁止明火→泄漏时立即关闭阀门并通风→禁止在密闭空间使用', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/252', '4'),
    ('氧气(Oxygen)', '强氧化剂;助燃;高压气瓶风险;油脂接触可自燃', '远离可燃物和油脂→禁止在氧气设备附近使用油脂→使用专用调节器→缓慢开启阀门→储存于专用气瓶区→远离易燃气体→泄漏时关闭阀门并通风', 'U.S. Occupational Safety and Health Administration', 'https://www.osha.gov/chemicaldata/420', '3'),
    ('乙炔(Acetylene)', '极易燃;爆炸性分解;不稳定;高压风险', '远离火源→始终直立存放→与氧气分开至少20英尺→使用回火防止器→使用专用调节器→禁止在铜配件中使用→低压力时更换→泄漏时关闭阀门并撤离', 'Cornell University Environment, Health and Safety', 'https://ehs.cornell.edu/research-safety/chemical-safety/laboratory-safety-manual/chapter-16-physical-hazards/164-compressed-gases', '5'),
    ('氯气(Chlorine)', '剧毒;强氧化剂;呼吸道严重刺激;腐蚀性', '必须在通风橱中操作→佩戴全面罩和专用手套→远离可燃物和还原剂→使用耐腐蚀设备→泄漏时立即撤离并向上风向转移→暴露后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/idlh/7782505.html', '5'),
    ('氨气(Ammonia)', '剧毒;强刺激性;呼吸道严重损伤;高压风险', '必须在通风橱中操作→佩戴全面罩和专用手套→远离卤素和氧化剂→使用耐腐蚀设备→泄漏时立即撤离→暴露后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/idlh/7664417.html', '4'),
    ('四氢呋喃(THF)', '易燃;麻醉作用;易形成过氧化物;爆炸风险', '远离火源→在通风橱中操作→佩戴PPE→使用防爆设备→储存于防火柜→添加抑制剂防止过氧化物形成→定期检查过氧化物→禁止蒸干', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0602.html', '4'),
    ('吡啶(Pyridine)', '易燃;剧毒;肝毒性;生殖毒性', '远离火源→在通风橱中操作→佩戴PPE→避免皮肤接触→储存于防火柜→大量泄漏时撤离→暴露后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0539.html', '4'),
    ('二甲基亚砜(DMSO)', '皮肤渗透促进剂;可携带其他化学品进入体内;生殖毒性', '佩戴专用手套→避免皮肤长期接触→在通风橱中操作→远离卤素和强氧化剂→储存于阴凉干燥处→皮肤接触后立即冲洗→孕妇避免接触', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0589.html', '3'),
    ('乙腈(Acetonitrile)', '易燃;剧毒;可释放氰化氢;吸入危害', '远离火源→在通风橱中操作→佩戴PPE→储存于防火柜→大量泄漏时撤离→暴露后立即就医→禁止在酸性条件下加热', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0008.html', '4'),
    ('三氟乙酸(TFA)', '强腐蚀性;吸入危害;皮肤灼伤;与金属反应产生氢气', '在通风橱中操作→佩戴PPE→使用耐腐蚀容器→远离金属粉末→储存于耐腐蚀区域→泄漏时用大量水稀释→皮肤接触后立即冲洗', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0626.html', '3'),
    ('碘(Iodine)', '腐蚀性;吸入危害;甲状腺影响;皮肤染色和刺激', '在通风橱中操作→佩戴PPE→避免皮肤接触→远离氨气和乙炔→储存于阴凉干燥处→皮肤接触后立即用硫代硫酸钠溶液冲洗', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0322.html', '3'),
    ('硝酸银(Silver Nitrate)', '强氧化剂;腐蚀性;光敏性;皮肤染色', '避光储存→在通风橱中操作→佩戴PPE→远离有机物和还原剂→使用耐腐蚀容器→皮肤接触后立即冲洗→泄漏时用沙土覆盖后收集', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0544.html', '3'),
    ('磷化氢(Phosphine)', '剧毒;自燃;爆炸性;致命风险', '必须在专用通风橱中操作→佩戴全面罩和专用手套→使用密闭系统→远离火源和氧化剂→泄漏时立即撤离→暴露后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0503.html', '5'),
    ('硅烷(Silane)', '剧毒;自燃;爆炸性;致命风险', '必须在专用通风橱中操作→佩戴全面罩和专用手套→使用密闭系统→远离火源和氧化剂→使用惰性气体保护→泄漏时立即撤离→暴露后立即就医', 'Centers for Disease Control and Prevention / NIOSH', 'https://www.cdc.gov/niosh/npg/npgd0554.html', '5'),
]

records = []
for name, hazards, steps, org, url, risk in CHEMICALS:
    records.append({
        'title': f'{name}实验室安全使用',
        'category': '化学',
        'question': f'实验室使用{name}时有哪些安全要求？',
        'answer': f'{name}的主要危害包括：{hazards}。安全操作步骤：{steps}。',
        'hazard_types': hazards,
        'steps': steps,
        'source_org': org,
        'source_url': url,
        'risk_level': risk,
    })

print(f'Generated {len(records)} chemical safety records')

with open('knowledge_base_curated.csv', 'r', encoding='utf-8-sig', newline='') as f:
    kb_rows = list(csv.DictReader(f))

existing_titles = set(r['title'].strip() for r in kb_rows if r.get('title'))
max_num = 0
for r in kb_rows:
    rid = r.get('id','')
    if rid.startswith('KB-CHEM2-'):
        try:
            num = int(rid.replace('KB-CHEM2-',''))
            max_num = max(max_num, num)
        except:
            pass

new_rows = []
skipped = 0
for rec in records:
    if rec['title'] in existing_titles:
        skipped += 1
        continue
    max_num += 1
    new_id = f'KB-CHEM2-{max_num:04d}'
    new_rows.append({
        'id': new_id,
        'title': rec['title'],
        'category': rec['category'],
        'subcategory': '',
        'lab_type': '化学',
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
        'reviewer': 'auto-ingest-chem2; pending human review',
        'status': 'draft',
        'tags': f'chem2_batch;{rec["category"]}',
        'language': 'zh-CN',
        'suspension_reason': '',
        'suspension_date': '',
    })

print(f'Existing KB: {len(kb_rows)}')
print(f'Duplicates skipped: {skipped}')
print(f'Records to import: {len(new_rows)}')

if new_rows:
    with open('knowledge_base_curated.csv', 'a', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=new_rows[0].keys())
        writer.writerows(new_rows)
    print(f'Successfully imported {len(new_rows)} records')
    print(f'New total: {len(kb_rows) + len(new_rows)}')
