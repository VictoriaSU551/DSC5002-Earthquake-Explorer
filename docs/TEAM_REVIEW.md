# 组员成果评审与最终整合（2026-11-10）

依据项目计划 `5002rp3.0.docx` 的五个研究问题评审。文档中的分工或
成员文件中的“应采用本次数据”等建议均作为待核验内容，没有当作额外指令执行。

## 统一口径

最终使用原项目冻结的 **46,463 条 earthquake 事件**，UTC
`[2000-01-01, 2026-01-01)`、preferred M≥5。所有主体结果使用同一快照。
数据 SHA256：`231b5b4fadf2d0d4eccfe4f03b8eb8489d225ff84e921f18d2b973af46d544ff`。
当前交付在 `outputs/final` 和 `deliverables`。后续 2.0 扩充与五列海报见
[EXPERIMENT_EXTENSION.md](EXPERIMENT_EXTENSION.md)；旧海报不另留版本。

## 各部分结论

| 投稿 | 评审结论 | 最终采用与修改 |
|---|---|---|
| Member 2 空间与统计 | 分析方向符合 RQ1、RQ2，但样本和解释有实质问题，不能原样采用 | 按冻结目录重算；使用精确球面大圆劣弧线段距离替代 25 km 离散采样；主体地区统一为项目六个框和 Other；保留描述性相关，取消未证实 M5 完备性的 b 值解读 |
| Member 3 深度与剖面 | 主要数值可复现，方法完整，可采用 | 合入源代码、七条有限条带剖面、地区深度图和 3D 视图；独立用距离/方位角算法核对 105 项；明确路线经过探索选择，不能当作随机代表性剖面 |
| Member 4 / HUANG Youkun 震级与频率 | 核验充分，主要采用 | 所有累计计数逐项重算；切换到主项目只读快照；修正 inclusive N(M≥m) 的阶梯连接方向；相对能量图保留为示意，不当作测得能量或损失 |
| RQ5 三案例与动画 | 计数和关键指标正确，可采用，但投稿缺少独立构建代码 | 从单文件 HTML 恢复动画源代码，与 RQ3 合并；新增可复现对比表；修正 Reset/拖动时不停播、tooltip 重复 km、重叠柱形等问题；去掉“背景活动”“最大余震”等未经识别的因果标签 |

### Member 2 的 60 条差额

其代码没有 `eventtype=earthquake` 查询参数，也没有本地类型筛选。
Member 4 提供的全年原始文件合计 46,523 条，其中
**55 条 volcanic eruption、4 条 nuclear explosion、1 条 landslide**。
筛选后 46,463 条记录的 ID、时间、经纬度、深度和震级与主项目完全一致。
这支持“事件类型口径差异”，不支持其报告的“60 条均为目录更新”解释。
Member 2 自己下载的原始文件未提交，因此不把 Member 4 的文件说成
Member 2 原始下载的逐字节副本。

### 其他解释修正

- 浅源/中源/深源：<70、70–<300、≥300 km；4 条负深度记录保留。
- 边界距离是对 PB2002 简化图层的球面距离，不是到所有活动断层的精确地质距离。
- pooled Spearman 接近零仅说明整体单调关联弱，不证明所有地区都无关系。
- RQ5 以精确锚点时刻划定 [-30,0)、[0,30) 日，半径 ≤500 km，锚点排除。
  地震依赖、空间窗口、震级门槛意味着不能直接推断因果或普遍余震规律。
- 相对能量代理量 `10^(1.5(M-5))` 使用混合震级，不能解释为实测焦耳或灾害风险。
- 全期 M5 Sen 斜率与两个时段均值比较方向不同，最终不宣传单一“上升/下降趋势”。

## 文件整合

全部 **98 个原始投稿文件**已从 `others` 移至 `local_sources/team_submissions/`，
逐文件核对 SHA256 后才删除空的 `others`。原稿属于审阅留档，不作为最终结论入口。
`submission_inventory.json` 记录原相对路径、大小及哈希。

- `earthquake_explorer/sections.py`：采用的 RQ3 球面剖面算法。
- `earthquake_explorer/magnitude_analysis.py`：整合后的 RQ4 分析。
- `web/dashboard.*`、`web/style.css`：整合后的 RQ3/RQ5 交互源代码。
- `run_final.py`：只读使用冻结快照生成整合结果。
- `outputs/final/`：当前报告、仪表盘、表、RQ4 图、海报图、验证记录。
- `deliverables/`：最终可搜索海报、讲稿和预览。
- `START_HERE.html`：本地总入口。

## 海报与讲稿参考落实

已读取 [CityU 海报样本](https://www.cityu.edu.hk/lc/app/academic-samples1.html)
及其 [multimodal features](https://www.cityu.edu.hk/lc/app/academic-multimodal-features.html)。
采用研究结构、短句和文本分块、编号、分栏、统一颜色、图注与参考资料。
这些页面**没有规定纸张尺寸或横竖方向**；A0 横版是本次排版选择。
标题、方法、结果、局限和结论均使用可搜索文字，图形采用矢量为主。

[讲稿样本](https://www.cityu.edu.hk/lc/app/poster-script-samples1.html)用作
开场、自我介绍、顺序提示、方法、发现与结尾致谢的参考，不复制其故事。
附约 6–7 分钟讲稿，这一时长是排练建议，**不是课程硬性要求**。
用户没有提供完整作者名单，因此署名 DSC5002 Project Team，没有虚构姓名。

## 复现

先按主项目说明建立本地数据缓存。已存在的已验证缓存不需重复下载。

```powershell
python run_final.py
python scripts/member3_analysis.py outputs/final/dashboard.html --output-dir outputs/final/tables
python scripts/expand_analysis.py
python scripts/verify_expansion.py
python scripts/build_poster_charts.py
python scripts/verify_rq3.py
python -m pytest -q
```

最新五列海报用案例计数表与静态累计曲线展示时间过程，不再采用动画截图或链接。
使用安装了 ReportLab、pypdf、Pillow 的 Python 执行
`scripts/build_poster_pdf.py`。本机使用 Codex bundled PDF runtime，无需改变分析环境。
海报设计固定对应上述已审阅快照；不同快照需重新核验文字与数值。

原始投稿的审计另用 `python scripts/audit_submissions.py`，只在持有本地投稿包时运行。
原稿、原始目录与完整观察级分析数据不上传；公开最新版海报、代码、汇总图表和报告。
来源许可见 THIRD_PARTY.md。最新构建完整顺序见上述扩充说明。
