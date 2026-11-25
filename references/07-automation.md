# 自动化操作手册（2026-11-24/25 实测）

执行浏览器操作前必读。工具：browser-skill 的 bsk CLI。环境准备（daemon 后台启动、客户端命令带 `BSK_AUTO_START=0`、动作被拒时 `bsk sync --json` 取 observation_id 重放、无障碍树缺元素时用 CSS 选择器兜底、目检用截图+Read）与百度版 `tool-sidehustle/references/07-automation.md` §0 相同。

## 1. 5118 小红书挖词（需 5118 登录）

- 落地页：`https://www.5118.com/ci/xhs`（首页「小红书挖词→关键词挖掘」链接同样可达）
- 结果页：`https://www.5118.com/xhs/words/<token>`，标题格式「<实际命中词> 小红书长尾关键词挖掘」
- **标题按后缀匹配**：5118 会把查询词扩展成关联短语（「简历制作」→「简历制作-免费模板…|在线制作个人简历」），匹配「小红书长尾关键词挖掘」结尾并把实际命中词记入 CSV 的 matched_title 列
- **token 跨平台通用**：同词 token 在 `/seo/newwords/`（全网）、`/douyin/words/`（抖音）、`/xhs/words/`（小红书）通用
- 总量解析：vom「相关小红书长尾词共找到」前 ~25 行内的 emphasis 数字节点；小红书版一个节点（总量），全网版两个（总量+有指数）
- 输入框选择器依次尝试：`input[type='text']:not([placeholder*='关键词'])` → `input[type='text']` → `input[placeholder*='搜索']`；点击「关键词挖掘」后等 ≥6s 再 fill
- 页面提示弹窗用 `button "确定"` 关闭后继续
- 结果表含流量指数/笔记数（虚拟渲染，行级精确值走 API；总量经 vom 解析即可用）

## 2. 小红书搜索联想词（需小红书登录）

- 搜索页：`https://www.xiaohongshu.com/search_result?keyword=<词>`（登录态直接可用）
- 驱动脚本 `scripts/xhs_suggest.py`：open 结果页 → fill 搜索框（textbox「搜索小红书」，值=词+空格触发联想）→ vom 抓 `button` 型条目 → 去渲染空格 → 过滤 UI 噪声（更多/关于我们/全部/图文/视频/用户/综合/tabbtnright/纯数字等，实测 185 条中 55 条为此类）
- 联想清单分两类，各有用途：**长句联想**（含种子词，= 笔记选题）与**筛选词标签**（短修饰词：免费/电脑版/无需会员，= 标题组合素材）
- 未登录时搜索框定位失败，脚本报 FAIL no search box → 请用户登录

## 3. 搜索结果页目检

- 笔记流为虚拟渲染，采用截图+视觉读取：每词截一次（前 9-12 篇），记录头部点赞中位数/内容形态/账号类型/筛选词标签/评论区呼声
- 截图要求目标 tab 前台可见；**截图后核对文件时间戳**，未更新则等待重试
- 滚动加载：bsk press PageDown 后分段截图

## 4. 节奏纪律

- 搜索/联想采集间隔 ≥3s；大批量查询分批进行
- 需要用户配合（登录/保持窗口前台）时说明原因并给预计时长
