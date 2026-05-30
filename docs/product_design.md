# 产品设计说明书

本目录存放项目架构、技能 SDK、安全策略和产品规划文档。

完整产品设计来自仓库根目录 README 中的架构说明，核心目标是构建一个：

> 本地 AI 自监督执行平台。它以本地模型作为总控大脑，连接浏览器、桌面、文件、终端、搜索、代码代理和外部 AI 服务。

## MVP 范围

- Web 任务控制台
- FastAPI 后端
- 本地 LLM 连接器：LM Studio / Ollama / OpenAI-compatible
- 核心 Agent 循环：目标理解 → 规划 → 能力缺口 → 技能路由 → 执行 → 证据 → 验证 → 报告
- 技能系统：Shell / File / Browser / Desktop / External AI / Search / Visual Review / Self Verify
- 证据板和任务报告

## 后续路线

1. Tauri 桌面壳
2. 插件 SDK 完善
3. 更强的权限确认系统
4. 外部 AI 网页自动化登录态管理
5. 多模型交叉验证
6. 沙盒和回滚能力增强
