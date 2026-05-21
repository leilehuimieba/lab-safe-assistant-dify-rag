# 实验室安全数据重新采集规范

**制定时间**: 2026-05-21  
**背景**: 本次清理移除了434条来源不可追溯/不可靠的新增数据，需重新补充。  
**目标**: 补充约 **450条** 高质量、来源可追溯的实验室安全知识条目。

---

## 一、当前知识库状态

| 批次 | 清理前 | 保留 | 需补充 |
|------|--------|------|--------|
| 高校手册SDS | 128 | **128** | 0 ✅ |
| 前处理生物通用 | 151 | **134** | ~17 |
| 危废特定危害 | 142 | **124** | ~18 |
| 应急PPE | 111 | **97** | ~14 |
| 分析仪器 | 107 | **19** | ~88 ⚠️ |
| 标准文档 | 97 | **13** | ~84 ⚠️ |
| 辐射激光电气机械 | 120 | **11** | ~109 ⚠️ |
| 培训制度通用 | 104 | **0** | ~104 ⚠️ |
| **合计** | 960 | **526** | **~434** |

**重点补充领域**：分析仪器、辐射激光电气机械、培训制度通用、标准文档（这四个领域占需补充量的90%）。

---

## 二、来源准入标准（强制）

### ✅ 允许的来源类型

| 优先级 | 来源类型 | 示例 | 要求 |
|--------|----------|------|------|
| P0 | 政府权威机构官网 | OSHA、CDC、NIH、EPA、NRC、IAEA | 必须提供具体页面URL |
| P0 | 国际标准组织 | ISO、ANSI、IEC、WHO | 必须提供标准号+官方URL或PDF链接 |
| P0 | 中国国家标准 | GB、GB/T | 必须提供标准号+全国标准信息公共服务平台链接 |
| P1 | 知名高校EHS官网 | ehs.berkeley.edu, ehs.cornell.edu, ehs.harvard.edu | 必须提供具体页面URL |
| P1 | 中国高校公开安全手册 | 清华/北大/浙大/中山等官方公开版 | 必须提供官网PDF链接 |
| P1 | 知名厂商官方文档 | Agilent、Thermo、Waters、Shimadzu、PerkinElmer | 必须提供官方支持页面URL或文档下载链接 |
| P2 | 专业学术数据库（公开访问） | PubMed Central (PMC)、NCBI、arXiv | 必须提供直接访问URL |
| P2 | 知名实验室安全组织 | ACS Division of Chemical Health and Safety、AIHA、ABSA | 必须提供具体页面URL |

### ❌ 禁止的来源类型

| 类型 | 示例 | 原因 |
|------|------|------|
| 博客/内容农场 | crazyforchem.com, chempedia.info, ziebaq.com | 非权威，内容可靠性无法验证 |
| 商业推广网站 | tjtywh.com, bisonlife.in, laboao.com | 以销售为目的，非中立信息 |
| 维修/生活社区 | ifixit.com, 知乎, 百度知道 | 非专业实验室安全来源 |
| 需登录平台 | ResearchGate（大部分页面）、LinkedIn | 非公开资源，用户无法验证 |
| 已失效/不可访问 | 返回404/403/超时的URL | 来源不可追溯 |
| 明确不可链接 | files-do-not-link.udc.edu | 字面意思不可引用 |
| 急救培训博客 | cprcertificationnow.com | 非实验室安全专业机构 |
| 未知商业PDF | 来源不明的免费PDF下载站 | 无法验证文档真实性 |

---

## 三、每条数据必须满足的字段要求

### 3.1 必填字段

| 字段 | 要求 | 示例 |
|------|------|------|
| `title` | 简洁准确，不含废话 | "GC载气钢瓶安全操作规范" |
| `category` | 使用现有分类体系 | 化学/生物/电气/物理/通用/废弃物/辐射/设备安全/培训/标准 |
| `subcategory` | 具体设备或场景 | "气相色谱仪GC" |
| `source_title` | 来源文档的完整名称 | "Agilent GC Operation Manual" |
| `source_org` | 发布机构，不能为空 | "Agilent Technologies" |
| `source_url` | **必须提供**，优先直接链接 | "https://www.agilent.com/..." |
| `references` | 完整的引用信息 | "Agilent Technologies. GC Operation Manual (2023)" |

### 3.2 source_url 获取规范

1. **首选直接链接**：来源页面的直接URL
2. **PDF文档**：提供官方PDF下载链接，或文档托管链接
3. **搜索引擎缓存不可接受**：不得使用Google Cache、百度快照等作为source_url
4. **无法找到直接链接时的处理**：
   - 如果是知名标准（如OSHA 29 CFR 1910.1450），提供官方法规页面URL
   - 如果是高校手册，提供该校EHS官网首页URL+手册名称
   - 如果是厂商文档，提供厂商支持网站首页URL+文档名称
   - **禁止**以"找不到链接"为由留空

### 3.3 内容质量要求

| 维度 | 要求 |
|------|------|
| 准确性 | 技术参数（温度、压力、浓度等）必须与来源一致 |
| 完整性 | 必须覆盖：危害识别 → 预防措施 → 操作步骤 → 应急处理 |
| 可操作性 | 步骤必须具体，避免"注意安全"等空泛表述 |
| 时效性 | 优先2020年后的来源，过时法规需标注版本年份 |

---

## 四、分领域补充指南

### 4.1 分析仪器（需补充~88条）

**推荐来源**：
- **厂商官方**：Agilent、Waters、Thermo Fisher、Shimadzu、PerkinElmer的官网支持文档
- **高校EHS**：Cornell EHS (ehs.cornell.edu)、Berkeley EHS、Stanford EH&S的仪器安全指南
- **专业组织**：ACS Division of CHAS的仪器安全资源

**重点设备**（按优先级）：
1. GC/GC-MS、HPLC/UPLC、IC/ICP-MS/OES（高优先级）
2. AAS、XRF/XRD、NMR、MS、TGA/DSC（中优先级）
3. FTIR/拉曼、BET、DLS/Zeta（低优先级）

**查找策略**：
```
搜索关键词: "site:agilent.com GC safety" OR "site:cornell.edu gas chromatography safety"
搜索关键词: "site:thermofisher.com HPLC safety guide"
搜索关键词: "site:ehs.berkeley.edu NMR safety"
```

### 4.2 辐射激光电气机械（需补充~109条）

**推荐来源**：
- **辐射**：NRC (nrc.gov)、University of Toronto EPS、IAEA GSR Part 3
- **激光**：ANSI Z136.1官方页面、OSHA Laser Hazards页面、Laser Institute of America
- **电气**：OSHA Electrical Safety、NFPA 70E、IEEE电气安全指南
- **机械**：OSHA Machine Guarding、Cornell EHS机械安全

**查找策略**：
```
搜索关键词: "site:nrc.gov radiation safety laboratory"
搜索关键词: "site:osha.gov laser hazards"
搜索关键词: "site:osha.gov electrical safety laboratory"
```

### 4.3 培训制度通用（需补充~104条）

**推荐来源**：
- **中国高校**：清华、北大、浙大、中山、武大等官方公开的实验室安全手册PDF
- **美国高校**：Cornell EHS、Berkeley EHS、Stanford EH&S的培训材料
- **政府法规**：教育部《高等学校实验室安全规范》、GB 19489、OSHA Lab Standard
- **专业组织**：ACS《Prudent Practices in the Laboratory》、NRC《Prudent Practices》

**查找策略**：
```
搜索关键词: "site:tsinghua.edu.cn 实验室安全手册 filetype:pdf"
搜索关键词: "site:moe.gov.cn 高等学校实验室安全规范"
搜索关键词: "site:cornell.edu laboratory safety training"
```

### 4.4 标准文档（需补充~84条）

**推荐来源**：
- **美国**：OSHA (osha.gov)、CDC (cdc.gov)、NIH (nih.gov)、EPA (epa.gov)
- **中国**：全国标准信息公共服务平台 (std.samr.gov.cn)、国家标准化管理委员会
- **国际**：ISO (iso.org)、IEC (iec.ch)、WHO (who.int)

**重点标准**：
- OSHA 29 CFR 1910.1450 (Lab Standard)
- CDC BMBL 6th Edition
- NIH Guidelines for Research Involving Recombinant or Synthetic Nucleic Acid Molecules
- GB 19489-2008 实验室生物安全通用要求
- GB/T 27476 检测实验室安全

**查找策略**：
```
搜索关键词: "site:osha.gov 29 CFR 1910.1450"
搜索关键词: "site:cdc.gov bmbl 6th edition"
搜索关键词: "site:std.samr.gov.cn GB 19489"
```

---

## 五、采集流程规范

### Step 1: 来源预筛选
- 使用上述"允许来源"列表筛选目标网站
- 先访问目标页面，确认URL可访问（200/301）
- 记录source_url、source_title、source_org

### Step 2: 内容提取
- 从来源页面提取安全信息
- 保持技术参数准确，不自行编造
- 如果是英文来源，翻译成中文时保留关键术语

### Step 3: 字段填充
- 必须填充：title、category、subcategory、hazards、safety_measures、source、source_url
- 尽量填充：procedures、emergency、ppe
- source_url **不能为空**

### Step 4: 自验证
- 再次访问source_url，确认链接有效
- 检查source_org是否已填写
- 检查content是否与来源一致

---

## 六、质量控制检查清单

每条数据在入库前必须通过以下检查：

- [ ] source_url 已填写且不为空
- [ ] source_url 可访问（curl返回200/301）
- [ ] source_org 已填写且不为空
- [ ] 来源不在"禁止来源"列表中
- [ ] title 简洁准确，不超过50字
- [ ] category 在现有分类体系中
- [ ] answer 包含具体、可操作的安全信息
- [ ] 技术参数（温度、压力、浓度等）与来源一致
- [ ] 数据不与现有知识库重复

---

## 七、交付格式

与上次一致，使用JSON格式，每个文件一个批次：

```json
[
  {
    "title": "GC载气钢瓶安全操作规范",
    "category": "大型分析仪器",
    "subcategory": "气相色谱仪GC",
    "hazards": ["高压气体泄漏", "钢瓶倾倒"],
    "safety_measures": ["钢瓶必须固定在专用支架上"],
    "procedures": {
      "pre_operation": ["检查钢瓶固定是否牢固"],
      "operation": ["监控载气流量和压力"],
      "post_operation": ["关闭钢瓶主阀"]
    },
    "emergency": "发生气体泄漏时立即关闭钢瓶阀门...",
    "ppe": ["安全眼镜", "防护手套"],
    "source": "Cornell University EHS",
    "source_url": "https://ehs.cornell.edu/...",
    "data_source_batch": "分析仪器"
  }
]
```

**新增强制字段**：`source_url`

---

## 八、验证脚本

采集完成后，运行以下脚本验证来源质量：

```bash
python scripts/validate_sources.py <collected_data.json>
```

验证项：
1. source_url 非空率 = 100%
2. source_url 可访问率 ≥ 90%
3. source_org 非空率 = 100%
4. 禁止来源检出率 = 0%

---

**执行优先级**：分析仪器 > 辐射激光电气机械 > 培训制度通用 > 标准文档
