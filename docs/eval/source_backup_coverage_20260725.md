# 知识库来源链接与本地备份覆盖审计（2026-07-25）

- 生成时间（UTC）：`2026-07-25T10:47:02.865997+00:00`
- 知识片段：**3009** 条；唯一来源链接：**716** 个
- 本次实测可打开：**352** 个；被站点/反爬拦截：**333** 个；网络错误：**31** 个
- 有本地原件或归档证据：**93** 个链接，覆盖 **1474** 条知识片段
- PDF 来源：**151** 个；有本地 PDF 原件：**31** 个；缺本地 PDF：**120** 个

## 结论口径

1. `blocked_or_forbidden` 只表示自动化访问被站点策略拦截，不能直接判定链接失效；需要浏览器抽样或更换官方镜像复核。
2. `network_error` 是当前网络下未完成验证的来源，不能算作已通过。
3. `archive_mirror` 表示保存了官方镜像/等效证据，不等同于原始 URL 的逐字节备份。
4. 当前不能宣称“所有来源都有本地备份”；PDF 原件覆盖率仍需继续提升。

## PDF 原件缺口（按影响片段数排序）

| 影响片段 | 实测状态 | 来源链接 |
|---:|---|---|
| 29 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3404LABORATORY-SAFETY-GUIDANCE.pdf |
| 11 | open | https://documents.thermofisher.com/TFS-Assets/CMD/manuals/Man-1R120706-0002-GC-MS-Q-Exactive-Man1R1207060002-EN.pdf |
| 11 | open | https://ehs.stanford.edu/wp-content/uploads/lab-chemical-safety-plan.pdf |
| 10 | blocked_or_forbidden | https://documents.thermofisher.com/TFS-Assets/CMD/manuals/Man-4820-3601-LC-Vanquish-UHPLC-Man48203601-EN.pdf |
| 9 | open | https://icp-ms.help.agilent.com/en/Learning/PDF/G8400-90016_Precautions.pdf |
| 7 | open | https://community.agilent.com/cfs-filesystemfile/__key/communityserver-discussions-components-files/23/G7446_2D00_35102B-Agilent-magnetic-Resonance-systems.pdf |
| 7 | open | https://icp-ms.help.agilent.com/en/Learning/PDF/G3666-90006_Precautions.pdf |
| 6 | open | https://ehs.stanford.edu/wp-content/uploads/Storage-Group-Poster.pdf |
| 6 | open | https://www-pub.iaea.org/MTCD/Publications/PDF/Pub1578_web-57265295.pdf |
| 6 | open | https://www.epa.gov/sites/default/files/2016-01/documents/hw-char.pdf |
| 5 | open | https://documents.thermofisher.com/TFS-Assets/MSD/Product-Information/Summit-UG.pdf |
| 5 | blocked_or_forbidden | https://osp.od.nih.gov/wp-content/uploads/NIH_Guidelines.pdf |
| 5 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3088.pdf |
| 4 | open | https://chemistry.unt.edu/system/files/tga_2_user_manual.pdf |
| 4 | open | https://documents.thermofisher.com/TFS-Assets/MSD/manuals/summit-lite-site-and-safety-en.pdf |
| 4 | open | https://reach.cdc.gov/sites/default/files/job-aids-resources/Crisis%20Response%20Toolkit.pdf |
| 4 | open | https://www.cdc.gov/niosh/docs/2007-107/pdfs/2007-107.pdf |
| 4 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3678.pdf |
| 4 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAFACTSHEET-LABORATORY-SAFETY-CHEMICAL-HYGIENE-PLAN.pdf |
| 3 | open | https://documents.thermofisher.com/TFS-Assets/CMD/brochures/sn-43363-icp-oes-aas-benefits-sn43363-en.pdf |
| 3 | open | https://documents.thermofisher.com/TFS-Assets/CMD/manuals/ii-1r120591-0001-isq-ec-ms-req-ii1r1205910001-en.pdf |
| 3 | open | https://ehs.berkeley.edu/sites/default/files/publications/compressed-gas-proper-use-booklet.pdf |
| 3 | open | https://smse.seu.edu.cn/_upload/article/2f/f2/c82ef33b4b0fa7e37d28e6e784be/e1702a0e-d3c7-4843-9d57-8a4c24093f9d.pdf |
| 3 | network_error | https://www.agilent.com/cs/library/usermanuals/public/7890B_Safety.pdf |
| 3 | open | https://www.bc.edu/content/dam/bc1/schools/mcas/Chemistry/pdf/research/nmr/NMR_Safety_Plan.pdf |
| 3 | open | https://www.cdc.gov/niosh/docket/archive/pdfs/NIOSH-159/0159-020109-Sheet404.pdf |
| 3 | open | https://www.epa.gov/sites/default/files/2015-07/documents/cont05.pdf |
| 3 | open | https://www.nrc.gov/docs/ML2014/ML20147A696.pdf |
| 3 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAFACTSHEET-LABORATORY-SAFETY-OSHA-LAB-STANDARD.pdf |
| 2 | open | https://iwaste.epa.gov/rpts/handbk4.pdf |
| 2 | open | https://reach.cdc.gov/sites/default/files/2025-07/Autoclave-Text-Version-UPDATED.pdf |
| 2 | open | https://sciex.com/content/dam/SCIEX/pdf/customer-docs/user-guide/safety-practices-guide-en.pdf |
| 2 | network_error | https://www.agilent.com/cs/library/primers/public/Best_Practice_LC_Operations.pdf |
| 2 | network_error | https://www.agilent.com/cs/library/usermanuals/public/7890A%20GC%20User%20Manual%20Collection.pdf |
| 2 | network_error | https://www.agilent.com/cs/library/usermanuals/public/user-manual-gcms-hydrogen-safety-q7003-90053-en-agilent.pdf |
| 2 | open | https://www.cdc.gov/niosh/docs/2014-102/pdfs/2014-102.pdf |
| 2 | blocked_or_forbidden | https://www.metrohm.com/content/dam/metrohm/shared/documents/manuals/89/89308001EN.pdf |
| 2 | open | https://www.nrc.gov/docs/ML0133/ML013330106.pdf |
| 2 | open | https://www.nrc.gov/docs/ML0809/ML080910098.pdf |
| 2 | open | https://www.nrc.gov/docs/ML2517/ML25175A081.pdf |
| 2 | open | https://www.nrc.gov/docs/ml1019/ML101900087.pdf |
| 2 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/FORMALDEHYDE-FACTSHEET.pdf |
| 2 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3071.pdf |
| 2 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3151.pdf |
| 2 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA4480.pdf |
| 2 | open | https://www.shimadzu.com/an/sites/shimadzu.com.an/files/pim/pim_document_file/others/16942/bgaz-4000-2007.pdf |
| 1 | open | http://ccc.chem.pitt.edu/wipf/papers&presentations/safety-manual.pdf |
| 1 | open | https://adrona.lv/wp-content/uploads/2023/08/TGA-4000-Specifiactions_English.pdf |
| 1 | open | https://assets.thermofisher.com/TFS-Assets/LSG/manuals/MAN0016959_GAHyPerformanceAPTSKit_UG.pdf |
| 1 | open | https://documents.thermofisher.com/TFS-Assets/CAD/Application-Notes/apex-te-mct-an64724-en.pdf |
| 1 | open | https://documents.thermofisher.com/TFS-Assets/LED/manuals/50155784-c-Thermo%20Scientific%20Sorvall%20ST%2016R-en.pdf |
| 1 | open | https://documents.thermofisher.com/TFS-Assets/LPD/Application-Notes/bsc-a2-b2-differences-appnote.pdf |
| 1 | open | https://documents.thermofisher.com/TFS-Assets/MSD/Technical-Notes/FL53370-gas-phase-ftir-smoke-toxicity-measurements.pdf |
| 1 | open | https://ehs.berkeley.edu/sites/default/files/publications/tcp-gas-program.pdf |
| 1 | open | https://ehs.stonybrook.edu/_pdfs/EHS_Policy_4.5_Laboratory_Chemical_Fume_Hood_Safety_Program.pdf |
| 1 | open | https://ehs.yale.edu/sites/default/files/files/biosafety-manual.pdf |
| 1 | open | https://greenlabs.caltech.edu/documents/29173/LC-125_Lab-Guidelines-and-Standards_RevC_US.pdf |
| 1 | open | https://lcc.sjtu.edu.cn/Assets/userfiles/sys_eb538c1c-65ff-4e82-8e6a-a1ef01127fed/files/sysgl/%E4%B8%8A%E6%B5%B7%E4%BA%A4%E9%80%9A%E5%A4%A7%E5%AD%A6%E4%B8%AD%E8%8B%B1%E5%9B%BD%E9%99%85%E4%BD%8E%E7%A2%B3%E5%AD%A6%E9%99%A2%E5%AE%9E%E9%AA%8C%E5%AE%A4%E5%AE%89%E5%85%A8%E4%B8%8E%E7%AE%A1%E7%90%86%E8%A7%84%E8%8C%83.pdf |
| 1 | open | https://nationalmaglab.org/media/gocoa0b5/sp-13-chemical-safety-procedure.pdf |
| 1 | open | https://nmr.chem.ucsb.edu/docs/Bruker_NMR_Manuals/user_manual_topspin_ts40.pdf |
| 1 | open | https://nmr.nd.edu/assets/432368/bruker_nmr_training_g.1.pdf |
| 1 | open | https://reagent.bjmu.edu.cn/file/20230414134400495_%E5%AE%9E%E9%AA%8C%E5%AE%A4%E5%AE%89%E5%85%A8%E6%89%8B%E5%86%8C%E5%8D%B0%E5%88%B7%E7%89%8820210610.pdf |
| 1 | open | https://stacks.cdc.gov/view/cdc/214551/cdc_214551_DS1.pdf |
| 1 | blocked_or_forbidden | https://tools.thermofisher.com/content/sfs/manuals/iCAP%206000%20Spectrometers%20Pre-Installation%20Manual%20v4%202.pdf |
| 1 | open | https://tuttnauer.com/sites/default/files/2021-10/Manual-Autoclaves-Cleaning_Weekly.pdf |
| 1 | open | https://www.acs.org/content/dam/acsorg/about/governance/committees/chemicalsafety/academic-safety-culture-report.pdf |
| 1 | open | https://www.acs.org/content/dam/acsorg/acs-webinars/2018/slides/2018-10-11-lab-safety-culture-slides.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/brochures/Getting_your_HPLC_Back_up_and_running_flyer.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/eseminars/public/gc-detector-design-troubleshooting-flame-ionization-fid-theory-basics-gas-flows-july212020.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/sitepreparationchecklists/7800_7900_ICP-MS_Site_Preparation_Checklist_Rev.B.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/sitepreparationchecklists/Agilent%208890%20GC%20Site%20Preparation%20Checklist.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/5971-6636_Atomic_Safety_Info_EN.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/9000_Operation.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/G1364E-User.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/G3430-90052%207890B_Maintaining%20Guide.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/user-guide-coverting-ei-gcms-instruments-5994-2312en-agilent.pdf |
| 1 | network_error | https://www.agilent.com/cs/library/usermanuals/public/usermanual-gc-operation-8890-g3540-90014-en-agilent.pdf |
| 1 | network_error | https://www.agilent.com/library/usermanuals/Public/G9214-90000_RapidFire360_User_RevD.pdf |
| 1 | open | https://www.birmingham.ac.uk/documents/college-eps/chemical/science-city/brochure-br010en-03-a-invia-confocal-raman-microscope-1.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2009-147/pdfs/2009-147-revised.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2011-199/pdfs/2011-199.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2011-200/pdfs/2011-200.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2012-123/pdfs/2012-123.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2023-139/pdfs/2023-139revised092023.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/2025-107/pdfs/2025-107.pdf |
| 1 | open | https://www.cdc.gov/niosh/docs/wp-solutions/2025-100/pdfs/2025-100.pdf |
| 1 | open | https://www.cdc.gov/niosh/hhe/reports/pdfs/1993-0802-2338.pdf |
| 1 | open | https://www.cdc.gov/niosh/hhe/reports/pdfs/1999-0313-2802.pdf |
| 1 | open | https://www.cdc.gov/niosh/hhe/reports/pdfs/2017-0114-3357.pdf |
| 1 | open | https://www.cdc.gov/niosh/hhe/reports/pdfs/74-7-270.pdf |
| 1 | open | https://www.cdc.gov/niosh/hhe/reports/pdfs/83-63-1364.pdf |
| 1 | open | https://www.csi.cuny.edu/sites/default/files/pdf/administration/finance/ehs/CSI_Chemical_Hygiene_Plan.pdf |
| 1 | open | https://www.nrc.gov/docs/ML0822/ML082280814.pdf |
| 1 | open | https://www.nrc.gov/docs/ML0827/ML082750235.pdf |
| 1 | open | https://www.nrc.gov/docs/ML1204/ML12044A227.pdf |
| 1 | open | https://www.nrc.gov/docs/ML1306/ML13064A088.pdf |
| 1 | open | https://www.nrc.gov/docs/ML1609/ML16090A100.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/2019-03/fireprotection.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/Job_Hazard_Analysis_Worksheet.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/enforcement/directives/CPL_02-01-065.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/enforcement/directives/PUB_8-1_5.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3172.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3780.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3908.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3909.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3912.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHA3918.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAfactsheet-laboratory-safety-chemical-hygiene-plan.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAfactsheet-metrics-in-psm.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAquickfacts-lab-safety-chemical-fume-hoods.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/OSHAquickfacts-lab-safety-labeling-chemical-transfer.pdf |
| 1 | blocked_or_forbidden | https://www.osha.gov/sites/default/files/publications/highly-hazardous-chemicals-factsheet.pdf |
| 1 | open | https://www.renishaw.com/resourcecentre/download/declaration-of-conformity-invia-raman-spectrometer--130961 |
| 1 | open | https://www.shimadzu.com/an/sites/shimadzu.com.an/files/pim/pim_document_file/brochures/16695/c122-e064.pdf |
| 1 | open | https://www.slu.edu/research/faculty-resources/-pdf/chemical_hygiene_plan.pdf |
| 1 | open | https://www.umb.edu.pl/photo/ftplib/Wydzialy/wnl/FTiA/ZnO/User%20manual%20Zetasizer.pdf |
| 1 | open | https://www.uoguelph.ca/hr/system/files/Laboratory%20Safety%20Manual.pdf |
| 1 | open | https://www.uwindsor.ca/chemical-control-centre/sites/uwindsor.ca.chemical-control-centre/files/lsm_2025.pdf |
| 1 | open | https://www.weizmann.ac.il/ChemicalResearchSupport/sites/ChemicalResearchSupport/files/bruker_magnet_safety_0.pdf |
| 1 | open | https://www.weizmann.ac.il/ChemicalResearchSupport/sites/ChemicalResearchSupport/files/bruker_refill_manual_0.pdf |
