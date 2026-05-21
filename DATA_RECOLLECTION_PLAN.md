# 实验室安全知识库数据重新采集计划

**制定时间**: 2026-05-21  
**当前状态**: 问题数据1,509条已提取至 `problem_sources.csv`，知识库剩余1,852条干净数据  
**目标**: 用权威来源补充被提取的数据缺口，逐步替换问题数据

---

## 一、现状与缺口分析

### 1.1 各领域缺口

| 领域 | 保留(干净) | 问题(已提取) | 缺口占比 | 优先级 |
|------|-----------|-------------|---------|--------|
| **化学** | 656 | 980 | **60%** | P0 |
| **设备安全** | 129 | 200 | **61%** | P0 |
| **通用** | 228 | 239 | **51%** | P0 |
| **废弃物** | 160 | 56 | 26% | P1 |
| **物理** | 45 | 11 | 20% | P1 |
| **标准** | 74 | 15 | 17% | P1 |
| **培训** | 37 | 5 | 12% | P2 |
| **电气** | 34 | 1 | 3% | P2 |
| **辐射** | 90 | 1 | 1% | P2 |
| **生物** | 316 | 0 | 0% | 已充足 |

### 1.2 问题数据细分（Top 10子类）

| 子类 | 问题数量 | 内容类型 | 建议来源 |
|------|---------|---------|---------|
| 应急 | 319 | 酸液泄漏、触电、火灾、化学品暴露等 | OSHA应急指南、Cornell EHS应急手册 |
| 危险化学品 | 269 | 强酸强碱、有毒化学品、易燃物操作 | NCBI Prudent Practices、OSHA化学安全 |
| 危险化学品安全 | 269 | 混合禁忌、储存规范、标签要求 | OSHA 29 CFR 1910.1200、CDC |
| 有机溶剂 | 13 | 乙醇、乙醚、丙酮等SDS | Sigma-Aldrich SDS、Merck SDS |
| 安全制度 | 11 | 培训制度、检查制度、准入制度 | 教育部规范、Cornell EHS制度 |
| 强酸强碱 | 11 | 硫酸、盐酸、氢氧化钠操作 | OSHA化学安全、NCBI Prudent Practices |
| 手套材质与化学品渗透 | 10 | 丁腈/乳胶/氯丁手套选择 | OSHA PPE指南、Ansell手套渗透数据库 |
| NIH rDNA Guidelines | 10 | 生物安全委员会、BL等级 | NIH rDNA指南官网 |
| 实验场景PPE | 9 | 配制溶液、高温操作PPE | OSHA PPE标准、NIH PPE指南 |
| 有毒化学品 | 9 | 汞、氰化物、砷操作 | NRC、OSHA、EPA |
| 废液桶管理 | 8 | 分类收集、标签、80%限制 | EPA RCRA、Cornell EHS危废手册 |

---

## 二、按领域补充策略

### P0 优先级：化学（需补充~980条）

**核心缺口**：应急处理（319条）、危险化学品操作（538条）、PPE（9条）、废液管理（8条）

**推荐来源（按优先级排序）**：

| 来源 | URL | 内容类型 | 预计可提取条数 |
|------|-----|---------|--------------|
| **OSHA Chemical Safety** | https://www.osha.gov/chemicals | 化学品安全通用要求、应急处理 | 100+ |
| **OSHA 29 CFR 1910.1200** | https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1200 | 危害通报标准（SDS/标签） | 30+ |
| **NCBI Prudent Practices Ch.5-7** | https://www.ncbi.nlm.nih.gov/books/NBK55884/ | 化学品处理、储存、废弃物 | 150+ |
| **Cornell EHS Chemical Safety** | https://ehs.cornell.edu/research-safety/chemical-safety | 化学品储存、相容性、应急 | 80+ |
| **NIH Chemical Safety Guide** | https://ors.od.nih.gov/sr/dohs/Documents/chemical-safety-guide.pdf | 危害分类、SDS、培训 | 50+ |
| **EPA RCRA Hazardous Waste** | https://www.epa.gov/hw | 危废分类、收集、处置 | 50+ |
| **Merck SDS Database** | https://www.merck.com/products/safety-data-sheets/ | 具体化学品SDS | 200+ |
| **Sigma-Aldrich SDS** | https://www.sigmaaldrich.com | 具体化学品SDS | 100+ |

**搜索策略**：
```
搜索1: site:osha.gov chemical spill emergency response laboratory
搜索2: site:ncbi.nlm.nih.gov/books/NBK55884 corrosive storage
搜索3: site:ehs.cornell.edu chemical compatibility storage
搜索4: site:epa.gov hazardous waste collection laboratory
```

---

### P0 优先级：设备安全（需补充~200条）

**核心缺口**：分析仪器操作安全（GC、HPLC、ICP、NMR、AAS等）

**推荐来源**：

| 来源 | URL | 内容类型 | 预计可提取条数 |
|------|-----|---------|--------------|
| **Agilent Safety Resources** | https://www.agilent.com/en/product/gas-chromatography-gc | GC/GC-MS安全 | 20+ |
| **Thermo Fisher Safety** | https://www.thermofisher.com/cn/zh/home.html | HPLC/ICP-MS/MS安全 | 20+ |
| **Shimadzu Safety** | https://www.shimadzu.com/an/gc/safety_function.html | GC安全功能 | 10+ |
| **Cornell EHS Equipment Safety** | https://ehs.cornell.edu/research-safety/equipment-safety | 通用设备安全 | 30+ |
| **NIH Equipment Safety** | https://ors.od.nih.gov/sr/dohs/Pages/Equipment-Safety.aspx | 高压、激光、辐射设备 | 20+ |
| **Bruker Safety Guides** | https://www.bruker.com/service/support-upgrades/safety.html | NMR/MS安全 | 10+ |
| **Waters Safety** | https://www.waters.com/waters/nav.htm?cid=513832 | UPLC/HPLC安全 | 10+ |

**搜索策略**：
```
搜索1: site:agilent.com GC safety site preparation hydrogen
搜索2: site:thermofisher.com HPLC safety operation manual
搜索3: site:shimadzu.com GC safety function
搜索4: site:ehs.cornell.edu equipment safety centrifuge autoclave
```

---

### P0 优先级：通用（需补充~239条）

**核心缺口**：安全制度、培训要求、标识规范、化学品相容性

**推荐来源**：

| 来源 | URL | 内容类型 | 预计可提取条数 |
|------|-----|---------|--------------|
| **教育部实验室安全规范** | http://www.moe.gov.cn/srcsite/A16/moe_784/202302/t20230220_1045998.html | 中国高校实验室管理制度 | 30+ |
| **Cornell EHS General Safety** | https://ehs.cornell.edu/research-safety/general-laboratory-safety | 通用实验室安全制度 | 40+ |
| **OSHA Laboratory Standard** | https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450 | 实验室标准（CHP） | 30+ |
| **NIH Chemical Hygiene Plan** | https://ors.od.nih.gov/sr/dohs/Documents/chemical-hygiene-plan.pdf | 化学卫生计划模板 | 30+ |
| **Berkeley EHS Safety Manual** | https://ehs.berkeley.edu/research-safety/laboratory-safety-manual | 实验室安全手册 | 30+ |
| **NCBI Prudent Practices Ch.1-2** | https://www.ncbi.nlm.nih.gov/books/NBK55882/ | 安全文化、责任体系 | 30+ |

**搜索策略**：
```
搜索1: site:moe.gov.cn 实验室安全规范 培训 制度
搜索2: site:ehs.cornell.edu laboratory safety manual training
搜索3: site:osha.gov laboratory standard 1910.1450 chemical hygiene plan
搜索4: site:ehs.berkeley.edu laboratory safety manual
```

---

### P1 优先级：废弃物（需补充~56条）

**推荐来源**：
- EPA RCRA: https://www.epa.gov/hw
- Cornell EHS Hazardous Waste: https://ehs.cornell.edu/research-safety/environmental-compliance/hazardous-waste
- Yale EHS Chemical Waste: https://ehs.yale.edu/environment-waste/waste-management/chemical-waste
- NIH Waste Management: https://ors.od.nih.gov/sr/dohs/Pages/Hazardous-Waste.aspx

**搜索策略**：
```
搜索: site:epa.gov hazardous waste laboratory disposal
搜索: site:ehs.cornell.edu hazardous waste disposal chemical
```

---

### P1 优先级：物理/辐射/电气（需补充~23条）

**推荐来源**：
- OSHA Laser Hazards: https://www.osha.gov/laser-hazards/hazards
- ANSI Z136.1官方购买页: https://webstore.ansi.org/standards/lia/ansiz1362022
- NRC Radiation Safety: https://www.nrc.gov/about-nrc/radiation/protects-you.html
- OSHA Electrical Safety: https://www.osha.gov/electrical
- IEEE Electrical Safety: https://ieeexplore.ieee.org/document/8784672

---

### P1 优先级：标准（需补充~15条）

**推荐来源**：
- 全国标准信息公共服务平台: https://std.samr.gov.cn/ 或 https://openstd.samr.gov.cn/
- OSHA标准库: https://www.osha.gov/laws-regs/regulations/standardnumber/1910
- CDC BMBL: https://www.cdc.gov/labs/bmbl/
- WHO实验室安全手册: https://www.who.int/publications/i/item/9789240011410

---

## 三、采集方法

### 方法A：官网直接采集（推荐）

1. 使用 `opencli web read --url <url> -f md` 获取页面内容
2. 从Markdown中提取安全信息
3. 按规范填充字段

### 方法B：站点适配器批量采集

对以下网站可编写适配器批量获取：
- OSHA官网（结构化法规页面）
- NCBI Books（在线书籍，章节结构清晰）
- Cornell EHS（手册章节结构清晰）

### 方法C：PDF文档解析

对以下PDF直接提取内容：
- NIH Chemical Hygiene Plan PDF
- NIH Chemical Safety Guide PDF
- CDC BMBL 6th Edition PDF
- Yale Laboratory Chemical Hygiene Plan PDF

---

## 四、质量控制红线

**以下数据绝不入库**：

1. ❌ source_url 为空
2. ❌ source_org 为空
3. ❌ 来源是博客/内容农场/商业推广网站
4. ❌ 来源URL不可访问（curl/opencli均失败）
5. ❌ 单页HTML被作为>10条不相关数据的来源
6. ❌ 技术参数与来源不一致
7. ❌ 内容与现有知识库重复

**入库前必须验证**：

- [ ] source_url 可访问（opencli success）
- [ ] source_org 已填写
- [ ] 来源不在禁止列表
- [ ] 内容是具体可操作的安全信息（非空泛表述）
- [ ] 数据不与现有知识库重复

---

## 五、分阶段执行计划

### 第一阶段（1-2周）：化学应急 + 危险化学品操作
**目标**: 补充400条
**来源**: OSHA化学安全、NCBI Prudent Practices、Cornell EHS化学安全
**重点**: 应急处理319条 + 危险化学品操作80条

### 第二阶段（1-2周）：设备安全
**目标**: 补充150条
**来源**: Agilent、Thermo、Shimadzu、Bruker、Waters官方安全文档
**重点**: GC/GC-MS、HPLC/UPLC、ICP-MS、NMR、AAS安全操作

### 第三阶段（1周）：通用安全制度
**目标**: 补充150条
**来源**: 教育部规范、Cornell EHS通用安全、OSHA实验室标准、Berkeley EHS
**重点**: 培训制度、检查制度、化学品标签、相容性矩阵

### 第四阶段（1周）：废弃物 + 物理/辐射/电气 + 标准
**目标**: 补充100条
**来源**: EPA、NRC、OSHA、ANSI官网、国家标准平台

**总目标**: 约800条，逐步替换 `problem_sources.csv` 中的问题数据

---

## 六、问题数据替换流程

1. 新数据导入后，与 `problem_sources.csv` 中同分类/同子类的记录对比
2. 如果新数据来源可靠且覆盖同一知识点，从 `problem_sources.csv` 中删除对应旧记录
3. 重复此流程，直到 `problem_sources.csv` 中对应领域的记录被清空
4. 最终完全删除 `problem_sources.csv`

---

## 七、立即可以开始的采集任务

以下来源已验证可访问，可立即开始：

| 来源 | URL | 预计条数 | 优先级 |
|------|-----|---------|--------|
| OSHA Chemical Safety | https://www.osha.gov/chemicals | 50+ | P0 |
| NCBI Prudent Practices | https://www.ncbi.nlm.nih.gov/books/NBK55884/ | 100+ | P0 |
| Cornell EHS Chemical | https://ehs.cornell.edu/research-safety/chemical-safety | 50+ | P0 |
| Agilent GC Safety | https://www.agilent.com/cs/library/usermanuals/public/9000_Operation.pdf | 15+ | P0 |
| Thermo GC-MS Manual | https://documents.thermofisher.com/.../Man-1R120706-0002-GC-MS... | 15+ | P0 |
| OSHA Lab Standard | https://www.osha.gov/laws-regs/regulations/standardnumber/1910/1910.1450 | 20+ | P0 |
| EPA Hazardous Waste | https://www.epa.gov/hw | 30+ | P1 |
| NRC Radiation Safety | https://www.nrc.gov/about-nrc/radiation/protects-you.html | 20+ | P1 |

需要我先帮你从其中哪个来源开始采集？
