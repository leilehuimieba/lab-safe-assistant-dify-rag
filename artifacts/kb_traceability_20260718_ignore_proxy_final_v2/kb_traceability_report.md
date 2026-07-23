# 知识库来源追溯与链接审计报告

- generated_at: `2026-07-18T14:54:22.071095+00:00`
- kb_path: `D:\newwork\Security\lab-safe-assistant-dify-rag\knowledge_base_curated.csv`
- row_count: `3009`
- unique_source_url_count: `716`
- missing_source_title_count: `0`
- missing_source_org_count: `0`
- missing_source_url_count: `0`
- invalid_source_url_count: `0`
- missing_risk_level_count: `0`
- invalid_risk_level_count: `0`
- missing_subcategory_count: `0`
- missing_references_count: `0`
- references_placeholder_count: `0`
- references_without_source_url_count: `0`

## 链接审计口径

- `open`: 当前网络下可访问，HTTP 2xx/3xx 且返回非空内容。
- `open_empty`: 当前网络下可访问，但抽样内容为空，需要人工确认是否为动态下载或空响应。
- `blocked_or_forbidden`: 链接存在但当前网络被 401/403/429 拒绝，优先寻找可公开访问的等价官方链接。
- `dead_or_moved`: 当前返回 404/410，必须替换为可打开的官方链接，或从知识库移除该来源贡献。
- `network_error`: 连接超时、TLS、远端重置等网络错误，需复查并缓存证据。

## 字段问题样例

| id | category | risk_level | issues | source_url |
|---|---|---|---|---|
| 无 | - | - | - | - |

## 来源域名 Top 20

| domain | rows |
|---|---:|
| ehs.cornell.edu | 493 |
| ors.od.nih.gov | 474 |
| www.osha.gov | 426 |
| www.cdc.gov | 361 |
| www.ncbi.nlm.nih.gov | 245 |
| ehs.yale.edu | 131 |
| nap.nationalacademies.org | 110 |
| www.epa.gov | 53 |
| ehs.berkeley.edu | 45 |
| ehs.stanford.edu | 43 |
| documents.thermofisher.com | 40 |
| www.nrc.gov | 39 |
| www.ehs.washington.edu | 37 |
| www.agilent.com | 32 |
| ehs.utexas.edu | 31 |
| openstd.samr.gov.cn | 29 |
| sbc.sysu.edu.cn | 27 |
| blink.ucsd.edu | 20 |
| www.merck.com | 19 |
| icp-ms.help.agilent.com | 16 |

## 全量 URL 检查汇总

- unique_urls_checked: `716`
- url_status_counts: `{'open': 339, 'blocked_or_forbidden': 336, 'network_error': 41}`
- affected_row_counts: `{'open': 2149, 'blocked_or_forbidden': 728, 'network_error': 132}`

## 需整改链接

| status | http | rows | orgs | url | error |
|---|---:|---:|---|---|---|
| blocked_or_forbidden | 403 | 1 | Cornell Law School (29 CFR Reference) | https://coactionspecialty.safetynow.com/chemical-compatibility-storage-guidelines-quick-tips/ |  |
| blocked_or_forbidden | 403 | 1 | University of Minnesota DEHS | https://dehs.umn.edu/biological-safety-cabinets |  |
| blocked_or_forbidden | 403 | 10 | Thermo Fisher Scientific | https://documents.thermofisher.com/TFS-Assets/CMD/manuals/Man-4820-3601-LC-Vanquish-UHPLC-Man48203601-EN.pdf |  |
| blocked_or_forbidden | 403 | 1 | Princeton Environmental Health and Safety | https://ehs.princeton.edu/laboratory-research/chemical-waste-management |  |
| blocked_or_forbidden | 429 | 1 | Bruker Corporation | https://ir.bruker.com/press-releases/press-release-details/2024/Bruker-Advances-Magnet-Technology-for-Broader-Adoption-of-NMR-in-Academic-and-Biopharma-Research-and-Process-Analytical-Technologies/default.aspx |  |
| network_error |  | 5 | Thermo Fisher Scientific | https://knowledge1.thermofisher.com/@api/deki/files/29093/Ver_1.02_-_iCAP_7000_Reference_Guide.pdf | ReadTimeout: HTTPSConnectionPool(host='files.mtstatic.com', port=443): Read timed out. (read timeout=15) |
| network_error |  | 3 | OSHA/NFPA;OSHA/NFPA参考 | https://makesafetyeasy.com/blog/chemical-storage-safety-guide | ReadTimeout: HTTPSConnectionPool(host='makesafetyeasy.com', port=443): Read timed out. (read timeout=15) |
| blocked_or_forbidden | 403 | 4 | PerkinElmer | https://manualmachine.com/perkinelmer/tga4000/2520538-user-manual/ |  |
| network_error |  | 13 | 住建部;国家市场监督管理总局;国家市场监督管理总局 / OSHA;国家市场监督管理总局 / 国务院;国家标准化管理委员会(SAC) | https://openstd.samr.gov.cn/ | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 3 | 国家市场监督管理总局/国家标准委 | https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=0E0C42CADDB0D3E8DA27FECB80CCDE02 | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 1 | 国家市场监督管理总局/国家标准委 | https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=9C6A99E26AE0CA7E47B4BC9E8DF01F84 | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 2 | 国家市场监督管理总局/国家标准委 | https://openstd.samr.gov.cn/bzgk/gb/newGbInfo?hcno=AEC2B0CFFC2BF1B8C7CF1888B77E2FE4 | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 1 | 国家标准全文公开系统 | https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=6C80C3CF343258529DA8841981A036D1 | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 1 | 国家标准全文公开系统 | https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=8BFEEBBE490CBAC79543F0DAD96F2E2E | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| network_error |  | 8 | 国家标准全文公开系统 | https://openstd.samr.gov.cn/bzgk/std/newGbInfo?hcno=EB3B94B543F6E4CD18C044DE6AB64CEC | ConnectionError: ('Connection aborted.', RemoteDisconnected('Remote end closed connection without response')) |
| blocked_or_forbidden | 403 | 2 | NIH / CBD;National Institutes of Health | https://osp.od.nih.gov/biotechnology/nih-guidelines/ | ConnectionError: HTTPSConnectionPool(host='osp.od.nih.gov', port=443): Read timed out. |
| blocked_or_forbidden | 403 | 5 | NIH | https://osp.od.nih.gov/wp-content/uploads/NIH_Guidelines.pdf | ConnectionError: HTTPSConnectionPool(host='osp.od.nih.gov', port=443): Read timed out. |
| network_error |  | 2 | Metrohm | https://products.metrohm.com/eps/930-compact-ic-flex-6132 | SSLError: HTTPSConnectionPool(host='products.metrohm.com', port=443): Max retries exceeded with url: /eps/930-compact-ic-flex-6132 (Caused by SSLError(SSLCertVerificationError(1, "[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: Hostname mismatch, certificate is not valid for 'products.metrohm.com'. (_ssl.c:1032)"))) |
| blocked_or_forbidden | 403 | 1 | American Chemical Society (Journal of Chemical Health & Safety) | https://pubs.acs.org/doi/10.1016/j.jchas.2018.05.002 |  |
| blocked_or_forbidden | 403 | 2 | American Chemical Society | https://pubs.acs.org/doi/10.1021/acs.jchemed.5b00511 |  |
| blocked_or_forbidden | 403 | 1 | UCSF Radiology | https://radiology.ucsf.edu/patient-care/patient-safety/mri-safety-guidelines/access-restriction |  |
| blocked_or_forbidden | 403 | 1 | Thermo Fisher Scientific | https://tools.thermofisher.com/content/sfs/manuals/iCAP%206000%20Spectrometers%20Pre-Installation%20Manual%20v4%202.pdf |  |
| blocked_or_forbidden | 403 | 1 | ANSI/AIHA | https://webstore.ansi.org/standards/aiha/ansiz9.5 |  |
| blocked_or_forbidden | 403 | 1 | American National Standards Institute | https://webstore.ansi.org/standards/lia/ansiz13612014 |  |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/brochures/Getting_your_HPLC_Back_up_and_running_flyer.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/eseminars/public/gc-detector-design-troubleshooting-flame-ionization-fid-theory-basics-gas-flows-july212020.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 2 | Agilent Technologies | https://www.agilent.com/cs/library/primers/public/Best_Practice_LC_Operations.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/sitepreparationchecklists/7800_7900_ICP-MS_Site_Preparation_Checklist_Rev.B.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/sitepreparationchecklists/Agilent%208890%20GC%20Site%20Preparation%20Checklist.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/5971-6636_Atomic_Safety_Info_EN.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 2 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/7890A%20GC%20User%20Manual%20Collection.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 3 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/7890B_Safety.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/9000_Operation.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/G1364E-User.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/G3430-90052%207890B_Maintaining%20Guide.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/user-guide-coverting-ei-gcms-instruments-5994-2312en-agilent.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 2 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/user-manual-gcms-hydrogen-safety-q7003-90053-en-agilent.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/cs/library/usermanuals/public/usermanual-gc-operation-8890-g3540-90014-en-agilent.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/atomic-spectroscopy/atomic-absorption/aas-resource-hub | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/atomic-spectroscopy/atomic-absorption/atomic-absorption-background-correction-lamps/deuterium-lamps | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/atomic-spectroscopy/atomic-absorption/atomic-absorption-hollow-cathode-lamps | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/atomic-spectroscopy/inductively-coupled-plasma-mass-spectrometry-icp-ms/icp-ms-instrument-accessory-supplies/tools-manuals-for-icp-ms | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/atomic-spectroscopy/inductively-coupled-plasma-mass-spectrometry-icp-ms/icp-ms-instruments/7800-icp-ms | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/hplc-detectors | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/solvent-management-for-hplc/stay-safe-caps-accessories-for-hplc | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/hplc-systems | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/hplc-systems/preparative-hplc-systems/1290-infinity-ii-preparative-lc-msd-system | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/mass-spectrometry-lc-ms | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/en/product/liquid-chromatography/mass-spectrometry-lc-ms/infinitylab-lc-msd-series | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| network_error |  | 1 | Agilent Technologies | https://www.agilent.com/library/usermanuals/Public/G9214-90000_RapidFire360_User_RevD.pdf | ConnectionError: ('Connection aborted.', ConnectionResetError(10054, '远程主机强迫关闭了一个现有的连接。', None, 10054, None)) |
| blocked_or_forbidden | 403 | 1 | Beckman Coulter | https://www.beckman.com/landing/centrifuges/optima-x |  |
| blocked_or_forbidden | 401 | 1 | Bruker Corporation | https://www.bruker.com/en/news-and-events/newsletter/2021/first-newsletter-february-2021.html |  |
| blocked_or_forbidden | 403 | 1 | CDC (Centers for Disease Control and Prevention) | https://www.cdc.gov/bird-flu/php/severe-potential/guidelines-for-laboratory-biosafety.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/chemical-threats-and-toxins-laboratory/about/index.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/chemical-threats-and-toxins-laboratory/php/story/chemical-terrorism-preparation.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/eis/field-epi-manual/chapters/Epi-lab-Collaboration.html |  |
| blocked_or_forbidden | 403 | 1 | CDC | https://www.cdc.gov/laboratory-systems/php/about/index.html |  |
| blocked_or_forbidden | 403 | 27 | CDC/NIH | https://www.cdc.gov/labs/BMBL.html |  |
| blocked_or_forbidden | 403 | 5 | Centers for Disease Control and Prevention;Centers for Disease Control and Prevention / National Institutes of Health | https://www.cdc.gov/labs/bmbl.html |  |
| blocked_or_forbidden | 403 | 8 | CDC | https://www.cdc.gov/labs/bmbl/ |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIH;Centers for Disease Control and Prevention (CDC) / NIH | https://www.cdc.gov/labs/bmbl/index.html |  |
| blocked_or_forbidden | 403 | 1 | CDC | https://www.cdc.gov/labs/index.html |  |
| blocked_or_forbidden | 403 | 1 | CDC | https://www.cdc.gov/mmWR/preview/mmwrhtml/00001222.htm |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/mmwr/preview/mmwrhtml/00001761.htm |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/mmwr/preview/mmwrhtml/00016258.htm |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/mmwr/preview/mmwrhtml/00026209.htm |  |
| blocked_or_forbidden | 403 | 14 | CDC (Centers for Disease Control and Prevention);Centers for Disease Control and Prevention;Centers for Disease Control and Prevention (CDC);Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/mmwr/preview/mmwrhtml/su6101a1.htm |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention | https://www.cdc.gov/monkeypox/php/laboratories/biosafety.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/bulletin/2015/tank-gauging.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/bulletin/2016/noise.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/bulletin/2026/contaminated-ff-gear.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/chemicals/ |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docket/archive/docket295.html |  |
| blocked_or_forbidden | 403 | 1 | NIOSH/CDC | https://www.cdc.gov/niosh/docs/2007-107/default.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/2013-145/default.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/2021-112/default.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/87-104/default.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/hazardcontrol/hc24.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/hazardcontrol/hc26.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/docs/mining/works/coversheet2222.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/engcontrols/ecd/detail28.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/about.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/default.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750006.html |  |
| blocked_or_forbidden | 403 | 2 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750007.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750012.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750013.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750021.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750024.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750025.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750027.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750030.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750031.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/ershdb/emergencyresponsecard_29750035.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/exposure-banding/about/ |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/hhe/ |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/107131.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/630080.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/67561.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/71432.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/idlh/7439976.html |  |
| blocked_or_forbidden | 403 | 2 | Centers for Disease Control and Prevention (CDC) / NIOSH;Centers for Disease Control and Prevention / NIOSH | https://www.cdc.gov/niosh/idlh/7664417.html |  |
| blocked_or_forbidden | 403 | 2 | Centers for Disease Control and Prevention (CDC) / NIOSH;Centers for Disease Control and Prevention / NIOSH | https://www.cdc.gov/niosh/idlh/7782505.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/7783064.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/79016.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/idlh/79061.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/8030306.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention / NIOSH | https://www.cdc.gov/niosh/idlh/cyanides.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/idlh/default.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH | https://www.cdc.gov/niosh/idlh/intridl4.html |  |
| blocked_or_forbidden | 403 | 3 | CDC/NIOSH | https://www.cdc.gov/niosh/nano/about/index.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/npg/default.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/npg/firstaid.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/npg/nengapdxa.html |  |
| blocked_or_forbidden | 403 | 1 | Centers for Disease Control and Prevention (CDC) / NIOSH | https://www.cdc.gov/niosh/npg/nengapdxc.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention / NIOSH | https://www.cdc.gov/niosh/npg/npgd0004.html |  |
| blocked_or_forbidden | 403 | 2 | CDC/NIOSH;Centers for Disease Control and Prevention / NIOSH | https://www.cdc.gov/niosh/npg/npgd0008.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/npg/npgd0012.html |  |
| blocked_or_forbidden | 403 | 1 | CDC/NIOSH | https://www.cdc.gov/niosh/npg/npgd0028.html |  |
