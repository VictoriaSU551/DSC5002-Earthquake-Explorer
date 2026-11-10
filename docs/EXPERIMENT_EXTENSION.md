# 2.0 / 3.0 整合与五列海报（最新版）

本轮逐项比较 `5002rp草稿2.0.docx` 与 `5002rp3.0.docx`，保留 3.0 的五个研究问题、
统一冻结样本和组员成果审核，再恢复 2.0 中能提高解释力的分析。
文档中的分工、图数及视频数量设想作为计划内容评估，不作为用户额外指令。

| 2.0 中的方向 | 本轮落实 | 解释边界 |
|---|---|---|
| 面积公平的空间对照 | 65,536 个等面积球面参照点；再加 16,384 个纬度分布控制点 | 全地球含海洋；地理参照而非真实地震发生模型 |
| 地区与分层关联 | 地区边界邻近占比和 8×3 Spearman 热图 | 不使用把聚集地震当独立观测的显著性检验 |
| 相对能量刻度 | 事件数占比与 `10^(1.5(M−5))` 总和占比并列 | 混合震级，不是实测焦耳、损失或风险 |
| 事件过程及敏感性 | 同轴日计数、标准化累计曲线、3×3 半径/时窗网格 | 精确时间/距离选样，不证明因果余震归属 |
| 丰富空间与深度展示 | 等面积全球图、两个局部地图与等公里剖面、深度组成图 | 路线经过探索选择；没有垂直夸张 |
| 3D、旋转地球、动画 | 交互工具仍可探索；海报采用直接回答问题的静态图 | 海报不放非必要动画链接，不追求视频数量 |
| ShakeMap / PAGER | 本轮未新增 | 未取得并核验事件产品，不能推导震感、死亡或损失 |

## 新增空间参照的可复现定义

等面积设计为独立扰乱的二维 Sobol 序列，种子 5002、5003、5004、5005，各 `2^14`
点；经度为 `360u−180`，纬度为 `asin(2v−1)`。纬度控制种子 5012，经度仍均匀，
纬度由观测经验分布的逆分位数取得。因此均匀的是球面面积，不是纬度。
两类参照与地震使用相同 PB2002 图层和精确球面大圆劣弧距离算法，半径
6,371.0088 km。缓存绑定输入、几何/采样源码、样本量、种子以及 NumPy/SciPy 版本。

100 km 内：地震 **70.1504%**，等面积参照 **9.4177%**，纬度控制 **10.5042%**。
占比比值 **7.4488**。等面积四次设计为 **9.3750–9.5337%**；它是数值敏感性范围，
不是置信区间。没有由此计算 p 值、因果效应或地震风险倍数。
50/200/500 km 的结果见 `final_results/tables/spatial_reference_summary.csv`。

## 海报设计与 CityU 样本

[海报样本](https://www.cityu.edu.hk/lc/app/academic-samples1.html)及
[多模态说明](https://www.cityu.edu.hk/lc/app/academic-multimodal-features.html)用于研究结构、
短段落、分栏、图文配合、颜色一致性、编号与引用的参考；
[讲稿样本](https://www.cityu.edu.hk/lc/app/poster-script-samples1.html)用于开场、顺序提示、
方法、发现与结尾。页面没有指定 A0、横版或展示时长。本项目选择 A0 横版，
五列依次为研究设计、空间参照、时间可比性、深度关联、震级与事件序列。
正文约 22 pt；六张可搜索表格呈现样本口径与核心比较，五组精选主图呈现空间、趋势、剖面和累计时间过程。
摘要、研究动机、方法、结果讨论和局限构成完整叙述。完整报告保留全部 14 组研究图。
讲稿约 6–7 分钟（排练建议）。未提供完整作者名单，使用团队署名。

## 复现顺序

已有冻结缓存时不要重新下载。新克隆先按 README 建立基础数据；USGS 未来修订的
下载可能不是本次快照，不能沿用写死的海报数值。

```powershell
python -m pip install -r requirements.txt -r requirements-poster.txt
python run_final.py
python scripts/member3_analysis.py outputs/final/dashboard.html --output-dir outputs/final/tables
python scripts/expand_analysis.py
python scripts/verify_expansion.py
python scripts/build_poster_charts.py
python scripts/build_poster_pdf.py
python scripts/verify_poster_pdf.py
pdftoppm -scale-to 3200 -png -singlefile deliverables/DSC5002_Academic_Poster.pdf outputs/final/poster_preview
python scripts/package_final.py
python -m pytest -q
```

ReportLab / pypdf / Pillow 可在独立 Python 环境执行 PDF 构建与核验。
投稿与 RQ3 的既有审计凭证只在本地存在时附入公开包，不是新克隆构建的必需输入。
需要重新核验 RQ3 时，执行 `python scripts/verify_rq3.py`；安装 Playwright 并设置
`PLAYWRIGHT_MODULE` 和 `PLAYWRIGHT_BROWSER_CHANNEL=msedge` 后执行
`node scripts/rq3_browser_acceptance.cjs`。投稿审计 `scripts/audit_submissions.py`
只适用于持有未公开原始投稿的本机。既有审计与本轮新核验在 FINAL_VALIDATION 中区分。
在发布前人工检查 Poppler 渲染、图例、坐标、页脚链接、讲稿分页，并运行
`scripts/current_delivery_smoke.cjs` 检查报告和主页。
`package_final.py` 只发布当前图表、汇总表与核验凭证，清除发布目录内不再采用的生成物。
完整原始数据、投稿和采样缓存留在本地。旧海报直接覆盖，不另建旧版海报留档。

方法来源：[USGS 震级与能量说明](https://www.usgs.gov/programs/earthquake-hazards/earthquake-magnitude-energy-release-and-shaking-intensity)、
[SciPy Sobol 文档](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.qmc.Sobol.html)、
[Bird (2003), PB2002](https://doi.org/10.1029/2001GC000252)。
