# 🧠 Local AI Self-Supervised Orchestrator

> 📖 不熟悉命令行？请看 → [QUICK_START.md](QUICK_START.md)

> 本地 AI 自监督总控系统 — 让能力有限的本地模型学会借助更强工具、外部 AI 和电脑环境来完成复杂任务。

**macOS 三步启动：** 双击 `1_安装环境.command` → `3_运行体检.command` → `2_启动项目.command`

**Windows 三步启动：** 双击 `1_安装环境.bat` → `3_运行体检.bat` → `2_启动项目.bat`

**图形启动器：** 双击 `打开启动器.command`(Mac) 或 `打开启动器.bat`(Win)，或在终端执行 `python launcher.py`

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✅ Final-version blueprint status

This repository is a **runnable MVP + final product blueprint** aligned with the complete product design document.

- Runnable now: FastAPI backend, Web workbench, local LLM connector, core agent loop, built-in Skills, Evidence Board, verifier, failure handler, reporter.
- Final blueprint included: architecture docs, security policy, Skill SDK, external AI workspace design, desktop app roadmap, coverage checklist.
- Final effects modules added: persistent browser profiles, External AI Web Operator, Desktop Visual Operator, confirmation queue, sandbox, plugin loader, task recovery, goal-level verifier, failure repair planner.
- Two-dimensional strategy revision added: Goal Contract + Authorization Contract, `goal_mode × authorization_mode`, full-autonomy preflight, contract-based Agent entrypoint, and frontend dual selectors.
- Contract runtime upgrade added: Clarification Session, `/ws/execute-contract`, dynamic Preflight, action-risk confirmation, contract verifier, and failure taxonomy.
- Local Model Optimization Layer added: context budgeting, JSON repair, step state, evidence retrieval, tool-result summarization, retry policy, and external AI escalation for weak local models.
- See: [`docs/local_model_optimization.md`](docs/local_model_optimization.md), [`docs/two_dimensional_strategy.md`](docs/two_dimensional_strategy.md), [`docs/contract_runtime_upgrade.md`](docs/contract_runtime_upgrade.md), [`docs/coverage_checklist.md`](docs/coverage_checklist.md), [`docs/final_effects_coverage.md`](docs/final_effects_coverage.md), [`docs/final_blueprint.md`](docs/final_blueprint.md), [`docs/architecture.md`](docs/architecture.md).

## 📋 产品定位

这不是一个普通的聊天机器人或桌面自动化脚本。它是：

- 🤖 **本地 AI 总控运行时** — 以本地模型为大脑，协调所有工具
- 🔧 **多工具 AI 执行平台** — 浏览器、桌面、文件、终端、代码一体化
- 👁️ **自我监督的 Agent** — 会判断能力缺口，主动向更强 AI 求助
- 📊 **证据化执行系统** — 每一步都有证据，不靠"我觉得完成了"

## 🏗️ 核心架构

```
User Task
   ↓
Goal Strategy
   ├── Clarify First
   └── Autonomous Goal
   ↓
Goal Contract
   ↓
Authorization Strategy
   ├── Standard Authorization
   └── Full Autonomy Authorization
   ↓
Authorization Contract
   ↓
Local Model Optimization Layer
   ├── Context Window Manager
   ├── Prompt Builder
   ├── JSON Repair Parser
   ├── Step State Manager
   ├── Evidence Retriever
   ├── Tool Result Summarizer
   ├── External AI Escalation Router
   ├── Prompt Profiles
   ├── Model Capability Registry
   └── Retry Policy
   ↓
Planner / Skill Router / Verifier / Failure Handler
   ↓
Skill Execution Layer
   ↓
Evidence Board
   ↓
Reporter
```

## ✨ 7 大核心能力

| 能力                  | 描述                                       |
| --------------------- | ------------------------------------------ |
| 🎯 **会理解任务**     | 把模糊需求转化为明确目标和完成标准         |
| 🤔 **会判断能力不足** | 识别自身能力缺口，知道什么时候需要帮助     |
| 🆘 **会主动求助**     | 根据任务类型选择最合适的外部 AI 或工具     |
| 💻 **会操作电脑**     | 浏览器、桌面、文件、终端全方位操作         |
| 🔄 **会处理失败**     | 错误分类、诊断、修复、重试，不会一失败就停 |
| ✅ **会自我校验**     | 用证据验证每一步是否真的成功               |
| 📝 **会输出报告**     | 完整的执行报告，包含做了什么、为什么、证据 |

## 🚀 最简单本地运行方式

### macOS / Linux

```bash
# 1. 一键安装
./scripts/local_setup_mac.sh

# 2. 检查环境
python3 scripts/doctor.py

# 3. 启动
./scripts/start_local.sh
```

### Windows

```powershell
# 1. 一键安装
.\scripts\local_setup_windows.ps1

# 2. 检查环境
python scripts/doctor.py

# 3. 启动
.\scripts\start_local_windows.ps1
```

打开 http://localhost:8422

### 常见错误

| 错误            | 解决                                            |
| --------------- | ----------------------------------------------- |
| LM Studio 没开  | 打开 LM Studio，加载模型，确认端口 1234         |
| Ollama 没开     | `ollama serve` 然后 `ollama pull llama3`        |
| Playwright 没装 | `playwright install chromium`                   |
| 端口被占用      | 改 `.env` 中的 `PORT` 或用 `lsof -i :8422` 查看 |
| .env 缺失       | `cp .env.example .env` 然后编辑                 |
| `pip` 报错      | 确认在 venv 中：`source venv/bin/activate`      |

### 传统安装方式

```bash
git clone https://github.com/Dreaminmaster/local-ai-orchestrator.git
cd local-ai-orchestrator
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# 编辑 .env 配置本地模型
python -m backend.main
```

# 访问 Web 控制台

# 打开浏览器访问 http://localhost:8422

```

## 📁 项目结构

```

local-ai-orchestrator/
├── backend/
│ ├── main.py # FastAPI 入口
│ ├── api/ # API 路由
│ │ ├── tasks.py # 任务管理
│ │ ├── skills.py # 技能管理
│ │ └── websocket.py # WebSocket 实时通信
│ ├── core/ # 核心引擎
│ │ ├── agent.py # Agent 主循环
│ │ ├── goal_interpreter.py # 目标理解器
│ │ ├── planner.py # 任务规划器
│ │ ├── capability_gap.py # 能力缺口检测器
│ │ ├── skill_router.py # 技能路由器
│ │ ├── supervisor.py # 监督器
│ │ ├── verifier.py # 验证器
│ │ ├── failure_handler.py # 失败处理器
│ │ └── reporter.py # 报告生成器
│ ├── llm/ # LLM 提供者
│ │ ├── base.py # 基础接口
│ │ ├── lmstudio.py # LM Studio
│ │ ├── ollama.py # Ollama
│ │ └── openai_compat.py # OpenAI 兼容
│ ├── skills/ # 技能模块
│ │ ├── base.py # 技能基类
│ │ ├── browser_skill.py # 浏览器控制
│ │ ├── desktop_skill.py # 桌面控制
│ │ ├── external_ai_skill.py # 外部 AI
│ │ ├── file_skill.py # 文件操作
│ │ ├── shell_skill.py # 终端命令
│ │ ├── search_skill.py # 搜索引擎
│ │ ├── visual_review_skill.py # 视觉评审
│ │ └── self_verify_skill.py # 自我校验
│ ├── evidence/ # 证据系统
│ │ └── board.py # 证据板
│ ├── memory/ # 记忆系统
│ │ ├── task_memory.py # 任务记忆
│ │ └── user_preferences.py # 用户偏好
│ ├── prompts/ # 提示词模板
│ │ ├── goal_interpreter.md
│ │ ├── planner.md
│ │ ├── capability_gap.md
│ │ ├── verifier.md
│ │ ├── visual_review.md
│ │ ├── failure_handler.md
│ │ └── reporter.md
│ └── storage/ # 数据存储
│ └── database.py # SQLite 管理
├── frontend/ # Web 前端
│ ├── index.html # 任务控制台
│ ├── style.css # 样式
│ └── app.js # 前端逻辑
├── plugins/ # 自定义插件
│ └── README.md
├── docs/ # 文档
│ └── product_design.md
├── .env.example # 配置模板
├── requirements.txt # Python 依赖
├── pyproject.toml # 项目元数据
└── README.md

```

## 🎮 使用场景

### 场景 1：修网页设计

```

用户：帮我把这个网页做得更高级，不要低端模板感，自己检查效果。

系统自动执行：

1. 启动项目 → 2. 截图当前页面 → 3. 发给视觉模型评审
   → 4. 生成修改方案 → 5. 调 Codex 修改代码 → 6. 重新截图
   → 7. 对比前后效果 → 8. 不达标继续修 → 9. 输出修改报告

```

### 场景 2：修代码项目

```

用户：帮我把这个 GitHub 项目跑起来，报错自己解决。

系统自动执行：

1. 读取项目结构 → 2. 判断技术栈 → 3. 安装依赖
   → 4. 运行项目 → 5. 捕获报错 → 6. 问 Codex 修复
   → 7. 再运行 → 8. 截图验证 → 9. 输出修复记录

```

### 场景 3：研究复杂问题

```

用户：帮我分析有哪些项目可以实现 AI 控制电脑，给我组合方案。

系统自动执行：

1. 搜索 GitHub → 2. 读取 README → 3. 问 Claude 分析架构
   → 4. 问 ChatGPT 生成方案 → 5. 交叉比较 → 6. 输出最终方案

````

## ⚙️ 配置说明

### 本地模型

支持以下本地模型服务：

| 服务      | 配置                                                                      |
| --------- | ------------------------------------------------------------------------- |
| LM Studio | `LLM_PROVIDER=lmstudio`, `LLM_BASE_URL=http://localhost:1234/v1`          |
| Ollama    | `LLM_PROVIDER=ollama`, `LLM_BASE_URL=http://localhost:11434`              |
| vLLM      | `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL=http://localhost:8000/v1` |
| llama.cpp | `LLM_PROVIDER=openai_compatible`, `LLM_BASE_URL=http://localhost:8080/v1` |

### 外部 AI

在 `.env` 中配置外部 AI 的 API Key：

```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=...
````

## 🔒 安全设计

- **风险分级**：low / medium / high / critical，高风险动作必须用户确认
- **沙盒执行**：危险任务在隔离环境中运行
- **操作日志**：所有动作都有完整记录
- **回滚机制**：代码和文件修改前自动保存快照

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📄 License

MIT License
