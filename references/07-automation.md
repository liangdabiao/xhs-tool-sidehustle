# 自动化操作手册（2026-11-24 实测）

执行浏览器操作前必读。工具：browser-skill 的 bsk CLI。环境准备（daemon 后台启动、BSK_AUTO_START=0、observation 重试、CSS 选择器兜底、截图需前台可见）与百度版 `tool-sidehustle/references/07-automation.md` §0 相同，不重复。

## 1. 5118 小红书挖词（需 5118 登录）✅ 实测

- **落地页**：`https://www.5118.com/ci/xhs`（注意：`/xhs`、`/xhs/ci` 404，唯一正确路径 `/ci/xhs`；首页「小红书挖词→关键词挖掘」链接也可进）
- **结果页**：`https://www.5118.com/xhs/words/<token>`，标题「<词> 小红书长尾关键词挖掘」
- **驱动脚本**：`scripts/mine_5118_xhs.py`（fill `input[type='text']:not([placeholder*='关键词'])` → 点「搜 索」→ wait_root 标题 → vom emphasis 解析总量）
- **总量解析**：小红书版只有一个 emphasis 数字节点（长尾词总量）；全网版有两个（总量+有指数）。脚本已内置适配
- 实测：音频裁剪=514、markdown转word=4
- **token 跨平台通用**：同词 token 在 `/seo/newwords/`、`/douyin/words/`、`/xhs/words/` 通用（抖音版扩展成本极低）
- 字段：结果表含流量指数/笔记数（虚拟渲染 vom 读不到行级数据，精确值走 API；总量够用）

## 2. 小红书搜索联想词（需小红书登录）✅ 实测

- 搜索页：`https://www.xiaohongshu.com/search_result?keyword=<词>`（已登录直接可看）
- 驱动脚本：`scripts/xhs_suggest.py`——open 结果页 → fill 搜索框（textbox「搜索小红书」）→ 追加空格触发联想 → vom 抓 `button` 型条目 → 归一化（vom 字符间插空格）→ 过滤 UI 词（close/搜索/确定）
- 实测：「音频裁剪」34 条、「电脑剪视频」35 条
- 登录墙：未登录时搜索框定位失败，脚本会报 FAIL no search box——此时请用户登录

## 3. 小红书搜索结果页目检 ✅ 实测

- 笔记流虚拟渲染，vom 读不到卡片 → **截图 + 视觉读取**
- 可见信号：每篇笔记点赞数、作者名、发布时间；顶部**筛选词标签**（平台官方修饰词，挖词金矿）；图文/视频/用户 tab
- 截图要求 tab 前台可见（Agent Window 被切走即超时/留旧文件，核对时间戳）
- 滚动加载更多：需交互式滚动（bsk press PageDown）后分段截图，一次 9-12 篇足够

## 4. 频率与合规纪律

- 搜索/联想采集间隔 ≥3s；一天内同账号大批量查询控制总量
- 不自动点赞/关注/评论；不绕登录墙；不碰 API 签名（x-s/x-t）
- 需要用户配合时（登录/保持窗口前台）明确说明原因
