/* ============================================================
   Local AI Orchestrator — Frontend Logic
   ============================================================ */

const API_BASE = window.location.origin.includes("localhost")
  || window.__TAURI_INTERNALS__
  ? "http://localhost:8422"
  : window.location.origin;
const WS_BASE = API_BASE.replace(/^http/, "ws");

let ws = null;
let stepCount = 0;
let successCount = 0;
let failCount = 0;
let evidenceCount = 0;
let logCounter = 0;
let currentTaskId = "";
let pendingExternalAiTaskId = "";
let latestHealth = null;
let latestPlaywrightStatus = null;
let latestAppDataStatus = null;
let pendingRealProjectPreview = null;
let taskSubmissionInFlight = false;
let realProjectEventSource = null;
let realProjectStartedAt = 0;
let realProjectElapsedTimer = null;
const seenRealProjectEventIds = new Set();
const workspaceOpenRequests = new Map();
const providerWizardOrder = ["lmstudio", "claude", "chatgpt", "gemini", "kimi", "doubao"];
let providerWizardIndex = 0;
let latestProviderOverview = null;

const els = {
  llmStatus: document.getElementById("llmStatus"),
  llmStatusText: document.getElementById("llmStatusText"),
  goalDisplay: document.getElementById("goalDisplay"),
  criteriaList: document.getElementById("criteriaList"),
  aiProfiles: document.getElementById("aiProfiles"),
  webAiMatrix: document.getElementById("webAiMatrix"),
  webAiMatrixDetail: document.getElementById("webAiMatrixDetail"),
  webAiWorkspaceStatus: document.getElementById("webAiWorkspaceStatus"),
  playwrightStatus: document.getElementById("playwrightStatus"),
  firstRunStatus: document.getElementById("firstRunStatus"),
  appDataActionResult: document.getElementById("appDataActionResult"),
  backendStatus: document.getElementById("backendStatus"),
  portableStatus: document.getElementById("portableStatus"),
  lmStudioStatus: document.getElementById("lmStudioStatus"),
  externalAiStatus: document.getElementById("externalAiStatus"),
  desktopShellStatus: document.getElementById("desktopShellStatus"),
  currentTaskStatus: document.getElementById("currentTaskStatus"),
  externalAiPausePanel: document.getElementById("externalAiPausePanel"),
  externalAiPauseReason: document.getElementById("externalAiPauseReason"),
  skillsList: document.getElementById("skillsList"),
  taskInput: document.getElementById("taskInput"),
  executeBtn: document.getElementById("executeBtn"),
  planSteps: document.getElementById("planSteps"),
  logContainer: document.getElementById("logContainer"),
  logCount: document.getElementById("logCount"),
  reportArea: document.getElementById("reportArea"),
  reportContent: document.getElementById("reportContent"),
  evidenceBoard: document.getElementById("evidenceBoard"),
  statSteps: document.getElementById("statSteps"),
  statSuccess: document.getElementById("statSuccess"),
  statFailed: document.getElementById("statFailed"),
  statEvidence: document.getElementById("statEvidence"),
  taskMemory: document.getElementById("taskMemory"),
  goalMode: document.getElementById("goalMode"),
  authorizationMode: document.getElementById("authorizationMode"),
  projectPath: document.getElementById("projectPath"),
  externalAi: document.getElementById("externalAi"),
  userPreferences: document.getElementById("userPreferences"),
  protectedPaths: document.getElementById("protectedPaths"),
  capabilityGrid: document.getElementById("capabilityGrid"),
  preflightPanel: document.getElementById("preflightPanel"),
  clarificationPanel: document.getElementById("clarificationPanel"),
  clarificationSummary: document.getElementById("clarificationSummary"),
  clarificationQuestions: document.getElementById("clarificationQuestions"),
  pendingActionsList: document.getElementById("pendingActionsList"),
  resumableTasksList: document.getElementById("resumableTasksList"),
  recentTasksList: document.getElementById("recentTasksList"),
  localProviderCards: document.getElementById("localProviderCards"),
  webProviderCards: document.getElementById("webProviderCards"),
  productProviderMatrix: document.getElementById("productProviderMatrix"),
  providerRoutingPolicy: document.getElementById("providerRoutingPolicy"),
  providerAllowAutomatic: document.getElementById("providerAllowAutomatic"),
  providerRequireConfirmation: document.getElementById("providerRequireConfirmation"),
  providerMaxCalls: document.getElementById("providerMaxCalls"),
  providerPriority: document.getElementById("providerPriority"),
  localModelSimpleMode: document.getElementById("localModelSimpleMode"),
  localModelRoleSettings: document.getElementById("localModelRoleSettings"),
  disabledWebProviderCards: document.getElementById("disabledWebProviderCards"),
  realtimeStage: document.getElementById("realtimeStage"),
  realtimeStatus: document.getElementById("realtimeStatus"),
  realtimeProgress: document.getElementById("realtimeProgress"),
  realtimeElapsed: document.getElementById("realtimeElapsed"),
  realtimeClaudeCalls: document.getElementById("realtimeClaudeCalls"),
  providerEnabledCount: document.getElementById("providerEnabledCount"),
  providerVerifiedCount: document.getElementById("providerVerifiedCount"),
  providerDefaultLocal: document.getElementById("providerDefaultLocal"),
  providerDefaultExternal: document.getElementById("providerDefaultExternal"),
  providerOnboardingWizard: document.getElementById("providerOnboardingWizard"),
  providerChoiceGrid: document.getElementById("providerChoiceGrid"),
  providerWizardStep: document.getElementById("providerWizardStep"),
  providerWizardProgress: document.getElementById("providerWizardProgress"),
  providerPriorityList: document.getElementById("providerPriorityList"),
  taskProviderSummary: document.getElementById("taskProviderSummary"),
  providerWorkspaceConsole: document.getElementById("providerWorkspaceConsole"),
};

async function init() {
  await loadSystemHealth();
  await loadAppDataStatus();
  await loadSkills();
  await loadAiProfiles();
  await loadPendingConfirmations();
  await loadResumableTasks();
  await loadRecentTasks();
  await loadWebAiProfiles();
  await loadPendingExternalAi();
  await loadWebAiMatrix();
  await loadPlaywrightStatus();
  await loadProviderServices();
  await loadProviderWorkspaceConsole();
  renderFirstRunStatus();
  await refreshWorkspaceStatus("claude");
  initCapabilities();
  togglePreflight();
  connectWebSocket();
}

function showProductSection(section, button) {
  document.querySelectorAll(".product-nav-button").forEach((item) => item.classList.remove("active"));
  if (button) button.classList.add("active");
  const targets = {
    task: "task-section",
    history: "history-section",
    "external-ai": "external-ai-section",
    "ai-services": "ai-services-section",
    settings: "settings-section",
  };
  document.getElementById(targets[section])?.scrollIntoView({ behavior: "smooth", block: "start" });
}

async function loadSystemHealth() {
  const shellMode = window.__TAURI_INTERNALS__ ? "packaged / tauri" : "browser mode";
  if (els.desktopShellStatus) {
    els.desktopShellStatus.textContent = shellMode;
  }
  try {
    const res = await fetch(`${API_BASE}/api/health`);
    const data = await res.json();
    latestHealth = data;
    if (els.backendStatus) els.backendStatus.textContent = data.ok ? "running" : "unavailable";
    if (els.portableStatus) els.portableStatus.textContent = data.portable_mode ? "OK" : "warning";
    if (els.lmStudioStatus) els.lmStudioStatus.textContent = data.lmstudio_reachable ? "connected" : "disconnected";
    if (els.externalAiStatus) {
      const claude = data.external_ai?.claude?.state || "NOT_CONFIGURED";
      const chatgpt = data.external_ai?.chatgpt?.state || "NOT_CONFIGURED";
      els.externalAiStatus.textContent = `Claude ${claude} / ChatGPT ${chatgpt}`;
    }
    document.documentElement.dataset.appReady = "true";
    window.LOCAL_AI_UI_READY = true;
    await reportUiReady(shellMode);
    renderFirstRunStatus();
  } catch (e) {
    document.documentElement.dataset.appReady = "false";
    window.LOCAL_AI_UI_READY = false;
    if (els.backendStatus) els.backendStatus.textContent = "unavailable";
    if (els.portableStatus) els.portableStatus.textContent = "unknown";
    if (els.lmStudioStatus) els.lmStudioStatus.textContent = "unknown";
    if (els.externalAiStatus) els.externalAiStatus.textContent = "unknown";
  }
}

function currentShellMode() {
  if (window.__TAURI_INTERNALS__) {
    return window.location.protocol.startsWith("http") ? "tauri dev" : "packaged app";
  }
  if (window.location.origin.includes("localhost") || window.location.origin.includes("127.0.0.1")) {
    return "browser dev";
  }
  return "tauri dev";
}

function setupStatusItem(label, value, tone = "") {
  return `<div class="setup-status-item"><strong>${escapeHtml(label)}</strong><span class="${tone}">${escapeHtml(value)}</span></div>`;
}

function renderFirstRunStatus() {
  if (!els.firstRunStatus) return;
  const health = latestHealth || {};
  const appData = latestAppDataStatus || {};
  const playwright = latestPlaywrightStatus || {};
  const claude = health.external_ai?.claude?.state || "NOT_CONFIGURED";
  const chatgpt = health.external_ai?.chatgpt?.state || "NOT_CONFIGURED";
  const ollama = health.local_models?.ollama || {};
  const browserState = playwright.chromium_found ? "installed" : "missing";
  els.firstRunStatus.innerHTML = [
    setupStatusItem("Backend", health.ok ? "running" : "error", health.ok ? "success-text" : "warning-text"),
    setupStatusItem("App data", appData.app_data_dir || "checking..."),
    setupStatusItem("Project browser", browserState, playwright.chromium_found ? "success-text" : "warning-text"),
    setupStatusItem("Claude workspace", claude),
    setupStatusItem("ChatGPT workspace", chatgpt),
    setupStatusItem("LM Studio", health.lmstudio_reachable ? "connected" : "disconnected"),
    setupStatusItem("Ollama", ollama.enabled ? (health.ollama_reachable ? "connected" : "需要启动") : "未启用"),
    setupStatusItem("Current mode", currentShellMode()),
  ].join("");
}

async function loadAppDataStatus() {
  if (!els.firstRunStatus) return;
  try {
    const res = await fetch(`${API_BASE}/api/app-data/status`);
    latestAppDataStatus = await res.json();
    renderFirstRunStatus();
  } catch (e) {
    if (els.appDataActionResult) {
      els.appDataActionResult.innerHTML = `<p class="placeholder">本地数据状态加载失败: ${escapeHtml(e.message)}</p>`;
    }
  }
}

function showAppDataResult(message, tone = "") {
  if (!els.appDataActionResult) return;
  els.appDataActionResult.innerHTML = `<div class="memory-item ${tone}">${escapeHtml(message)}</div>`;
}

async function openAppData() {
  const res = await fetch(`${API_BASE}/api/app-data/open`, { method: "POST" });
  const data = await res.json();
  showAppDataResult(data.opened ? `已打开本地数据目录：${data.path}` : `无法打开目录：${data.reason || "unknown"}`);
}

async function exportDiagnostics() {
  const res = await fetch(`${API_BASE}/api/diagnostics/export`, { method: "POST" });
  const data = await res.json();
  showAppDataResult(data.success ? `诊断包已生成：${data.path}` : `诊断包生成失败：${data.error || "unknown"}`);
}

async function clearAppCache() {
  const confirmed = window.confirm("只清理临时文件、测试报告、pip 缓存和旧日志。不会删除设置、登录 profile、evidence 或任务。继续吗？");
  if (!confirmed) return;
  const res = await fetch(`${API_BASE}/api/app-data/clear-cache`, { method: "POST" });
  const data = await res.json();
  showAppDataResult(data.success ? "缓存清理完成，设置与登录状态已保留。" : `缓存清理失败：${data.error || "unknown"}`);
}

function showPlaywrightInstallHelp() {
  alert("项目专用浏览器将只安装到当前 App data / 项目专用目录，不使用系统 Playwright cache。点击“安装项目专用浏览器”后才会下载。");
}

function dismissPlaywrightNotice() {
  if (els.playwrightStatus) {
    els.playwrightStatus.innerHTML = '<div class="memory-item">已暂不安装。外部 AI 网页控制可能不可用。</div>';
  }
}

async function reportUiReady(shellMode) {
  try {
    await fetch(`${API_BASE}/api/ui-ready`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ready: true,
        frontend_loaded: true,
        health_panel_rendered: els.backendStatus?.textContent === "running",
        desktop_shell_mode: shellMode,
      }),
    });
  } catch (e) {
    console.warn("Failed to report UI readiness:", e);
  }
}

async function loadSkills() {
  try {
    const res = await fetch(`${API_BASE}/api/skills`);
    const data = await res.json();
    els.skillsList.innerHTML = "";
    data.skills.forEach((skill) => {
      const el = document.createElement("div");
      el.className = "skill-tag";
      el.textContent = skill.name;
      el.title = `${skill.description}\nRisk: ${skill.risk_level}`;
      els.skillsList.appendChild(el);
    });
  } catch (e) {
    console.error("Failed to load skills:", e);
  }
}

async function loadAiProfiles() {
  try {
    const res = await fetch(`${API_BASE}/api/ai-profiles`);
    const data = await res.json();
    els.aiProfiles.innerHTML = "";
    data.profiles.forEach((p) => {
      const el = document.createElement("div");
      el.className = "ai-profile-item";
      el.innerHTML = `
                <div class="ai-profile-dot ${p.status === "available" ? "available" : "unavailable"}"></div>
                <span>${p.name}</span>
            `;
      els.aiProfiles.appendChild(el);
    });
  } catch (e) {
    console.error("Failed to load AI profiles:", e);
  }
}

function connectWebSocket() {
  els.llmStatus.className = "status-dot connected";
  els.llmStatusText.textContent = "就绪";
}

function connectContractWebSocket(
  goalContract,
  authorizationContract,
  taskId = null,
) {
  return new Promise((resolve, reject) => {
    const contractWs = new WebSocket(`${WS_BASE}/ws/execute-contract`);
    contractWs.onopen = () => {
      els.llmStatus.className = "status-dot connected";
      els.llmStatusText.textContent = "Contract 流式执行中";
      const payload = taskId
        ? { task_id: taskId }
        : {
            goal_contract: goalContract,
            authorization_contract: authorizationContract,
          };
      contractWs.send(JSON.stringify(payload));
    };
    contractWs.onmessage = (event) => {
      const msg = JSON.parse(event.data);
      handleEvent(msg);
      if (["complete", "stopped", "need_user", "error"].includes(msg.type)) {
        contractWs.close();
        resolve(msg);
      }
    };
    contractWs.onerror = (err) => reject(err);
    contractWs.onclose = () => {
      els.llmStatusText.textContent = "就绪";
    };
  });
}

async function executeTask() {
  const input = els.taskInput.value.trim();
  if (!input) return;
  if (taskSubmissionInFlight) return;
  const projectPath = els.projectPath.value.trim();
  if (projectPath) {
    const signature = `${projectPath}\n${input}\n${els.goalMode.value}\n${els.authorizationMode.value}`;
    if (!pendingRealProjectPreview || pendingRealProjectPreview.signature !== signature) {
      await prepareRealProjectTask(input, projectPath, signature);
      return;
    }
    await executeRealProjectTask(input, projectPath);
    return;
  }
  resetUi();
  try {
    log(
      "生成 Goal Contract...",
      "phase",
      "🎯",
      new Date().toLocaleTimeString(),
    );
    const goalRes = await fetch(`${API_BASE}/api/task/prepare-goal`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        user_input: input,
        goal_mode: els.goalMode.value,
      }),
    });
    const preparedGoal = await goalRes.json();
    let goalContract = preparedGoal.goal_contract || preparedGoal;
    if (preparedGoal.needs_clarification) {
      const session = preparedGoal.clarification_session;
      goalContract = await showClarificationPanel(session, input);
    }
    handleEvent({
      type: "goal_contract",
      data: { goal_contract: goalContract },
      timestamp: new Date().toISOString(),
    });
    renderGoalContract(goalContract);

    let preflightResult = null;
    if (els.authorizationMode.value === "full_autonomy") {
      const preflightRes = await fetch(
        `${API_BASE}/api/task/full-autonomy-preflight`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_input: input,
            goal_contract: goalContract,
          }),
        },
      );
      preflightResult = await preflightRes.json();
      renderDynamicPreflight(preflightResult);
    }

    log(
      "生成 Authorization Contract...",
      "phase",
      "🔐",
      new Date().toLocaleTimeString(),
    );
    const authRes = await fetch(`${API_BASE}/api/task/prepare-authorization`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildAuthorizationPayload(preflightResult)),
    });
    const authorizationContract = await authRes.json();
    handleEvent({
      type: "authorization_contract",
      data: { authorization_contract: authorizationContract },
      timestamp: new Date().toISOString(),
    });

    log(
      "通过 WebSocket 流式启动 Contract Agent...",
      "phase",
      "🚀",
      new Date().toLocaleTimeString(),
    );
    try {
      await connectContractWebSocket(goalContract, authorizationContract);
    } catch (wsError) {
      log(
        "WebSocket 失败，使用 REST fallback...",
        "warning",
        "↩️",
        new Date().toLocaleTimeString(),
      );
      const startRes = await fetch(`${API_BASE}/api/task/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          goal_contract: goalContract,
          authorization_contract: authorizationContract,
        }),
      });
      const started = await startRes.json();
      (started.events || []).forEach(handleEvent);
    }
  } catch (e) {
    log(
      `启动失败: ${e.message}`,
      "error",
      "💥",
      new Date().toLocaleTimeString(),
    );
  } finally {
    finishUi();
  }
}

async function prepareRealProjectTask(input, projectPath, signature) {
  taskSubmissionInFlight = true;
  els.executeBtn.disabled = true;
  els.executeBtn.innerHTML = '<span class="btn-icon">⏳</span> 正在准备...';
  log("扫描项目并生成 Goal Contract...", "phase", "🎯", new Date().toLocaleTimeString());
  try {
    const payload = buildRealProjectPayload(input, projectPath, false);
    const res = await fetch(`${API_BASE}/api/tasks/real-project/prepare`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const preview = await res.json();
    if (!res.ok || preview.status === "FAIL") {
      throw new Error(preview.failure_code === "PROJECT_PATH_NOT_FOUND" ? "项目路径不存在" : preview.failure_reason || "准备失败");
    }
    pendingRealProjectPreview = { signature, preview };
    renderRealProjectGoalContract(preview.goal_contract || {});
    renderRealProjectPlan(preview.plan || {});
    addEvidence("project_scan", `已扫描 ${preview.project_inspection?.file_count || 0} 个文件`, true);
    log("Goal Contract 和执行计划已准备，请确认后开始执行", "success", "✅", new Date().toLocaleTimeString());
    els.executeBtn.innerHTML = '<span class="btn-icon">▶</span> 确认 Goal Contract 并开始执行';
  } catch (e) {
    pendingRealProjectPreview = null;
    log(`准备失败: ${e.message}`, "error", "💥", new Date().toLocaleTimeString());
    finishUi();
  } finally {
    taskSubmissionInFlight = false;
    els.executeBtn.disabled = false;
  }
}

function buildRealProjectPayload(input, projectPath, confirmed) {
  return {
    project_path: projectPath,
    user_goal: input,
    goal_mode: els.goalMode.value,
    authorization_mode: els.authorizationMode.value,
    protected_paths: (els.protectedPaths.value || "").split(",").map((x) => x.trim()).filter(Boolean),
    external_ai_policy: "local_first_claude_only_when_needed",
    max_external_ai_calls: 1,
    user_confirmed_write: confirmed,
  };
}

async function executeRealProjectTask(input, projectPath) {
  taskSubmissionInFlight = true;
  resetUi();
  els.executeBtn.disabled = true;
  els.executeBtn.innerHTML = '<span class="btn-icon">⏳</span> 任务执行中';
  log(
    `创建真实项目任务：${projectPath}`,
    "phase",
    "📁",
    new Date().toLocaleTimeString(),
  );
  try {
    const res = await fetch(`${API_BASE}/api/tasks/real-project/async`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        ...buildRealProjectPayload(input, projectPath, true),
        submission_id: pendingRealProjectPreview?.signature || `${projectPath}:${input}`,
      }),
    });
    const result = await res.json();
    if (!res.ok || !result.task_id) {
      throw new Error(result.detail || result.failure_reason || "real_project_task_failed");
    }
    currentTaskId = result.task_id;
    if (els.currentTaskStatus) {
      els.currentTaskStatus.textContent = `${currentTaskId} · ${result.status}`;
    }
    log(result.duplicate_prevented ? "已复用正在执行的同一任务" : "任务已创建，开始接收实时事件", "success", "📡", new Date().toLocaleTimeString());
    connectRealProjectEvents(currentTaskId);
    pendingRealProjectPreview = null;
  } catch (e) {
    log(
      `真实项目任务启动失败: ${e.message}`,
      "error",
      "💥",
      new Date().toLocaleTimeString(),
    );
    taskSubmissionInFlight = false;
    finishUi();
  } finally {
    if (!realProjectEventSource) {
      taskSubmissionInFlight = false;
      finishUi();
    }
  }
}

function connectRealProjectEvents(taskId, afterEventId = 0) {
  if (realProjectEventSource) realProjectEventSource.close();
  seenRealProjectEventIds.clear();
  realProjectStartedAt = Date.now();
  clearInterval(realProjectElapsedTimer);
  realProjectElapsedTimer = setInterval(() => {
    if (els.realtimeElapsed) els.realtimeElapsed.textContent = `${Math.floor((Date.now() - realProjectStartedAt) / 1000)} 秒`;
  }, 1000);
  const suffix = afterEventId ? `?after=${afterEventId}` : "";
  realProjectEventSource = new EventSource(`${API_BASE}/api/tasks/${taskId}/events${suffix}`);
  realProjectEventSource.addEventListener("task_event", (message) => {
    const event = JSON.parse(message.data);
    if (seenRealProjectEventIds.has(event.event_id)) return;
    seenRealProjectEventIds.add(event.event_id);
    handleRealProjectEvent(event);
  });
  realProjectEventSource.onerror = () => {
    log("实时连接暂时中断，正在自动恢复", "warning", "↻", new Date().toLocaleTimeString());
  };
}

async function handleRealProjectEvent(event) {
  const labels = {
    task_created: "任务已创建",
    goal_contract_created: "目标契约已生成",
    authorization_confirmed: "执行授权已确认",
    planning_started: "正在规划",
    plan_created: "执行计划已生成",
    step_started: "开始执行步骤",
    tool_started: "正在调用工具",
    tool_output: "工具返回结果",
    file_changed: "文件已修改",
    verification_started: "正在验证",
    verification_result: "验证结果已返回",
    repair_started: "正在修复",
    repair_completed: "修复完成",
    checkpoint_created: "已创建检查点",
    task_paused: "任务已暂停",
    task_resumed: "任务已恢复",
    task_failed: "任务失败",
    task_completed: "任务完成",
    final_report_ready: "最终报告已生成",
  };
  const text = event.summary || labels[event.event_type] || "任务状态更新";
  log(text, event.status === "failed" ? "error" : event.event_type === "task_completed" ? "success" : "phase", event.status === "failed" ? "!" : "•", new Date(event.timestamp).toLocaleTimeString());
  if (els.realtimeStage) els.realtimeStage.textContent = event.stage || "执行中";
  if (els.realtimeStatus) els.realtimeStatus.textContent = taskStatusLabel(event.status || "running");
  if (els.realtimeProgress) els.realtimeProgress.textContent = `${Number(event.progress_percent || 0)}%`;
  if (els.currentTaskStatus) els.currentTaskStatus.textContent = `${event.task_id} · ${taskStatusLabel(event.status || "running")}`;
  if (event.event_type === "file_changed") addEvidence("changed_file", event.safe_payload?.path || text, true);
  if (event.event_type === "external_ai_started" && els.realtimeClaudeCalls) {
    els.realtimeClaudeCalls.textContent = String(Number(els.realtimeClaudeCalls.textContent || 0) + 1);
  }
  if (event.step_id) {
    const step = document.querySelector(`#step-${Number(String(event.step_id).replace("step_", ""))}`);
    if (step) {
      step.classList.toggle("active", event.event_type === "step_started");
      step.classList.toggle("completed", event.event_type === "step_completed");
      step.classList.toggle("failed", event.status === "failed");
    }
  }
  if (event.event_type === "plan_created" || event.event_type === "goal_contract_created") {
    const detail = await fetch(`${API_BASE}/api/tasks/${event.task_id}`).then((res) => res.json());
    renderRealProjectGoalContract(detail.task?.goal_contract || {});
    renderRealProjectPlan(detail.task?.plan || {});
  }
  if (event.event_type === "final_report_ready") await viewTaskReport(event.task_id);
  if (["task_completed", "task_failed", "task_paused"].includes(event.event_type)) {
    realProjectEventSource?.close();
    realProjectEventSource = null;
    clearInterval(realProjectElapsedTimer);
    taskSubmissionInFlight = false;
    finishUi();
    await loadRecentTasks();
  }
}

function renderRealProjectGoalContract(contract) {
  els.goalDisplay.innerHTML = `
    <div><strong>用户目标:</strong> ${escapeHtml(contract.user_goal || contract.final_goal || "")}</div>
    <div><strong>项目:</strong> ${escapeHtml(contract.project_path || "")}</div>
    <div><strong>预期结果:</strong> ${escapeHtml(contract.expected_outcome || "")}</div>
    <div style="margin-top:4px; font-size:12px; color:var(--text-secondary)">
      <strong>风险:</strong> ${escapeHtml(contract.risk_level || "—")} ·
      <strong>外部 AI 上限:</strong> ${Number(contract.max_external_ai_calls || 0)}
    </div>`;
  els.criteriaList.innerHTML = "";
  (contract.success_criteria || []).forEach((criterion) => {
    const li = document.createElement("li");
    li.textContent = criterion;
    els.criteriaList.appendChild(li);
  });
}

function renderRealProjectPlan(planData) {
  els.planSteps.innerHTML = "";
  (planData.plan || []).forEach((step, index) => {
    const stepEl = document.createElement("div");
    stepEl.className = `plan-step ${step.status === "completed" ? "completed" : ""}`;
    stepEl.id = `step-${index + 1}`;
    stepEl.innerHTML = `
      <div class="step-number">${index + 1}</div>
      <div class="step-content">
        <div>${escapeHtml(step.objective || "")}</div>
        <small>${escapeHtml(step.verification || "")}</small>
      </div>
      <div class="step-skills"><span class="skill-tag">${escapeHtml(step.tool || "")}</span></div>`;
    els.planSteps.appendChild(stepEl);
  });
}

let pendingClarificationResolve = null;
let pendingClarificationSession = null;
let pendingOriginalInput = "";

function showClarificationPanel(session, originalInput) {
  pendingClarificationSession = session;
  pendingOriginalInput = originalInput;
  els.clarificationPanel.classList.remove("hidden");
  els.clarificationSummary.textContent =
    "请回答以下问题，系统将据此生成 Goal Contract。";
  els.clarificationQuestions.innerHTML = (session.questions || [])
    .map(
      (q) => `
        <div class="clarification-card">
            <label>${escapeHtml(q.question)}</label>
            <textarea data-question-id="${q.id}" rows="2" placeholder="你的回答"></textarea>
            <small>${escapeHtml(q.reason || "")}</small>
        </div>`,
    )
    .join("");
  return new Promise((resolve) => {
    pendingClarificationResolve = resolve;
  });
}

async function submitClarificationAnswers() {
  const answers = Array.from(
    els.clarificationQuestions.querySelectorAll("textarea"),
  ).map((t) => ({ question_id: t.dataset.questionId, answer: t.value }));
  answers.forEach((a) =>
    addEvidence("clarification_answer", a.answer || "(empty)", true),
  );
  const res = await fetch(`${API_BASE}/api/task/confirm-goal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      clarification_session_id: pendingClarificationSession.id,
      answers,
    }),
  });
  const contract = await res.json();
  els.clarificationPanel.classList.add("hidden");
  pendingClarificationResolve(contract);
}

async function skipClarification() {
  els.clarificationPanel.classList.add("hidden");
  const res = await fetch(`${API_BASE}/api/task/prepare-goal`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      user_input: pendingOriginalInput,
      goal_mode: "autonomous",
    }),
  });
  const prepared = await res.json();
  pendingClarificationResolve(prepared.goal_contract || prepared);
}

function collectClarificationAnswers(session) {
  log(
    "目标确认模式：收集澄清问题回答",
    "warning",
    "❓",
    new Date().toLocaleTimeString(),
  );
  return (session.questions || []).map((q) => {
    const answer = window.prompt(q.question, "") || "";
    addEvidence("clarification_question", q.question, true);
    addEvidence("clarification_answer", answer || "(empty)", true);
    return { question_id: q.id, answer };
  });
}

function renderDynamicPreflight(preflight) {
  if (!preflight) return;
  if (Array.isArray(preflight.required_capabilities)) {
    els.capabilityGrid.innerHTML = preflight.required_capabilities
      .map(
        (c) =>
          `<label><input type="checkbox" class="capabilityCheck" value="${escapeHtml(c)}" checked> ${escapeHtml(c)}</label>`,
      )
      .join("");
  }
  addMemory(
    "Preflight required resources: " +
      (preflight.required_resources || []).join(", "),
  );
  addMemory(
    "Recommended external AI: " +
      (preflight.recommended_external_ai || []).join(", "),
  );
  (preflight.preflight_questions || []).forEach((q) =>
    addMemory("Preflight: " + q),
  );
}

function buildAuthorizationPayload(preflightResult = null) {
  return {
    authorization_mode: els.authorizationMode.value,
    provided_resources: {
      project_path: els.projectPath.value,
      user_preferences: els.userPreferences.value,
      browser_profiles: (els.externalAi.value || "")
        .split(",")
        .map((x) => x.trim())
        .filter(Boolean),
    },
    granted_capabilities: getSelectedCapabilities(),
    available_external_ai: (els.externalAi.value || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean),
    protected_paths: (els.protectedPaths.value || "")
      .split(",")
      .map((x) => x.trim())
      .filter(Boolean),
    preflight_result: preflightResult,
  };
}

function initCapabilities() {
  const caps = [
    "read_files",
    "write_files",
    "run_shell",
    "install_dependencies",
    "start_local_services",
    "operate_browser",
    "operate_desktop",
    "use_clipboard",
    "take_screenshots",
    "ask_external_ai",
    "share_diagnostics_with_external_ai",
    "modify_code",
    "autonomous_retry",
    "autonomous_repair",
  ];
  els.capabilityGrid.innerHTML = caps
    .map(
      (c) =>
        `<label><input type="checkbox" class="capabilityCheck" value="${c}" checked> ${c}</label>`,
    )
    .join("");
}

function getSelectedCapabilities() {
  return Array.from(document.querySelectorAll(".capabilityCheck:checked")).map(
    (x) => x.value,
  );
}

function togglePreflight() {
  if (!els.preflightPanel) return;
  els.preflightPanel.style.display =
    els.authorizationMode.value === "full_autonomy" ? "block" : "none";
}

function resetUi() {
  els.executeBtn.disabled = true;
  els.executeBtn.innerHTML = '<span class="btn-icon">⏳</span> 执行中...';
  els.goalDisplay.innerHTML = '<p class="placeholder">分析中...</p>';
  els.criteriaList.innerHTML = "";
  els.planSteps.innerHTML = "";
  els.logContainer.innerHTML = "";
  els.evidenceBoard.innerHTML = "";
  els.reportArea.style.display = "none";
  els.taskMemory.innerHTML = "";
  stepCount = 0;
  successCount = 0;
  failCount = 0;
  evidenceCount = 0;
  logCounter = 0;
  updateStats();
}

function handleEvent(event) {
  const { type, data, timestamp } = event;
  const time = new Date(timestamp).toLocaleTimeString();
  switch (type) {
    case "goal_contract":
      renderGoalContract(data.goal_contract);
      log("Goal Contract 已生成", "success", "📄", time);
      break;
    case "authorization_contract":
      log(
        `Authorization Contract 已生成：${data.authorization_contract.authorization_mode}`,
        "success",
        "🔐",
        time,
      );
      addEvidence(
        "authorization_contract",
        (data.authorization_contract.granted_capabilities || []).join(", "),
        true,
      );
      break;
    case "phase":
      log(data.message, "phase", "🔄", time);
      break;
    case "goal":
      renderGoal(data.goal);
      log("任务目标已解析", "success", "🎯", time);
      break;
    case "plan":
      renderPlan(data.plan);
      log(`生成执行计划，共 ${data.plan.total_steps} 步`, "info", "📋", time);
      break;
    case "local_model_status":
      log(data.message || `本地模型状态: ${data.status}`, "warning", "↩", time);
      if (els.llmStatusText) {
        els.llmStatusText.textContent = data.fallback_used
          ? "规则规划 fallback"
          : data.status;
      }
      break;
    case "step_start":
      if (data.task_id) {
        currentTaskId = data.task_id;
        if (els.currentTaskStatus) els.currentTaskStatus.textContent = currentTaskId;
      }
      updateStepStatus(data.step, "active");
      log(`[Step ${data.step}/${data.total}] ${data.goal}`, "info", "▶️", time);
      break;
    case "permission_blocked":
      log(`权限不足: ${data.reason}`, "warning", "🔒", time);
      break;
    case "gap_detected":
      log(`发现能力缺口: ${data.gap.gap_type}`, "warning", "⚠️", time);
      addMemory(`缺口: ${data.gap.gap_type}`);
      break;
    case "skills_selected":
      log(`调用技能链: ${data.chain.join(" → ")}`, "info", "🔧", time);
      break;
    case "step_result":
      handleStepResult(data, time);
      break;
    case "external_ai_need_user":
      pendingExternalAiTaskId = data.task_id || currentTaskId;
      if (els.externalAiPausePanel) els.externalAiPausePanel.classList.remove("hidden");
      if (els.externalAiPauseReason) {
        els.externalAiPauseReason.textContent = `${data.provider || "External AI"} 需要处理：${data.reason || ""}。${data.suggested_user_action || ""}`;
      }
      log(`外部 AI 需要用户处理: ${data.reason || ""}`, "warning", "🙋", time);
      break;
    case "external_ai_pending_saved":
      pendingExternalAiTaskId = data.task_id || pendingExternalAiTaskId;
      log(`已保存 pending external AI action: ${pendingExternalAiTaskId}`, "info", "💾", time);
      loadPendingExternalAi();
      break;
    case "external_ai_resume_started":
      log("外部 AI 恢复开始", "phase", "▶", time);
      break;
    case "external_ai_resume_success":
      log("外部 AI 恢复成功", "success", "✅", time);
      break;
    case "external_ai_resume_still_needs_user":
      log("外部 AI 仍需用户处理", "warning", "🙋", time);
      break;
    case "external_ai_resume_failed":
      log(`外部 AI 恢复失败: ${data.failure_reason || ""}`, "error", "❌", time);
      break;
    case "failure_repair":
      log(
        `失败诊断: ${data.repair.symptom || "unknown"}`,
        "warning",
        "🔧",
        time,
      );
      break;
    case "verification":
      log(
        data.result.verified ? "最终校验通过" : "最终校验未通过",
        data.result.verified ? "success" : "error",
        data.result.verified ? "✅" : "❌",
        time,
      );
      break;
    case "report":
      els.reportArea.style.display = "block";
      els.reportContent.textContent = data.report;
      log("生成最终报告", "info", "📝", time);
      break;
    case "complete":
      finishUi();
      if (els.currentTaskStatus) {
        els.currentTaskStatus.textContent = `${data.task_id || currentTaskId || "task"} · ${data.status || (data.verified ? "success" : "completed_unverified")}`;
      }
      log(
        `任务结束. 成功率: ${(data.success_rate * 100).toFixed(0)}%`,
        data.verified ? "success" : "warning",
        "🏁",
        time,
      );
      loadRecentTasks();
      break;
    case "stopped":
      finishUi();
      if (data.resume_payload?.task_id) {
        pendingExternalAiTaskId = data.resume_payload.task_id;
        if (els.currentTaskStatus) els.currentTaskStatus.textContent = pendingExternalAiTaskId;
      }
      log(`任务停止: ${data.reason}`, "warning", "🛑", time);
      break;
    case "need_user":
      finishUi();
      loadPendingConfirmations();
      log(`需要用户确认: ${data.reason}`, "warning", "🙋", time);
      break;
    case "error":
      finishUi();
      log(`系统错误: ${data.message}`, "error", "💥", time);
      break;
  }
}

function handleStepResult(data, time) {
  updateStepStatus(data.step, data.success ? "completed" : "failed");
  if (data.success) {
    successCount++;
    log(`步骤 ${data.step} 执行成功`, "success", "✅", time);
  } else {
    failCount++;
    log(`步骤 ${data.step} 执行失败`, "error", "❌", time);
  }
  stepCount++;
  updateStats();
  data.results.forEach((r) => {
    if (r.evidence && r.evidence.length)
      r.evidence.forEach((ev) => addEvidence(r.skill, ev, r.success));
    else if (r.result)
      addEvidence(r.skill, r.result.substring(0, 80) + "...", r.success);
    else if (r.error)
      addEvidence(r.skill, r.error.substring(0, 80) + "...", false);
  });
}

function finishUi() {
  els.executeBtn.disabled = false;
  els.executeBtn.innerHTML = pendingRealProjectPreview
    ? '<span class="btn-icon">▶</span> 确认 Goal Contract 并开始执行'
    : '<span class="btn-icon">▶</span> 生成 Goal Contract';
}

function renderGoalContract(contract) {
  els.goalDisplay.innerHTML = `
        <div><strong>目标理解策略:</strong> ${escapeHtml(contract.goal_mode || "")}</div>
        <div><strong>最终目标:</strong> ${escapeHtml(contract.final_goal || "")}</div>
        <div style="margin-top:4px; font-size:12px; color:var(--text-secondary)">
            <strong>假设:</strong> ${(contract.assumptions || []).map(escapeHtml).join("；")}
        </div>`;
  els.criteriaList.innerHTML = "";
  (contract.success_criteria || []).forEach((c) => {
    const li = document.createElement("li");
    li.textContent = c;
    els.criteriaList.appendChild(li);
  });
}

function renderGoal(goal) {
  els.goalDisplay.innerHTML = `
        <div><strong>目标:</strong> ${escapeHtml(goal.main_goal || "")}</div>
        <div style="margin-top:4px; font-size:12px; color:var(--text-secondary)">
            <strong>类型:</strong> ${escapeHtml(goal.task_type || "general")} | <strong>复杂度:</strong> ${escapeHtml(goal.estimated_complexity || "medium")}
        </div>`;
  els.criteriaList.innerHTML = "";
  (goal.success_criteria || []).forEach((c) => {
    const li = document.createElement("li");
    li.textContent = c;
    els.criteriaList.appendChild(li);
  });
}

function renderPlan(planData) {
  els.planSteps.innerHTML = "";
  (planData.plan || []).forEach((step) => {
    const stepEl = document.createElement("div");
    stepEl.className = "plan-step";
    stepEl.id = `step-${step.step}`;
    const skillsHtml = (step.needed_skills || [])
      .map((s) => `<span class="skill-tag">${escapeHtml(s)}</span>`)
      .join("");
    stepEl.innerHTML = `<div class="step-number">${step.step}</div><div class="step-content"><div>${escapeHtml(step.goal || "")}</div></div><div class="step-skills">${skillsHtml}</div>`;
    els.planSteps.appendChild(stepEl);
  });
}

function updateStepStatus(stepNum, status) {
  const el = document.getElementById(`step-${stepNum}`);
  if (el) el.className = `plan-step ${status}`;
}

function log(msg, type = "info", icon = "•", time = "") {
  const el = document.createElement("div");
  el.className = `log-entry ${type}`;
  el.innerHTML = `<span class="log-time">[${time}]</span><span class="log-icon">${icon}</span><span class="log-text">${escapeHtml(msg)}</span>`;
  els.logContainer.appendChild(el);
  els.logContainer.scrollTop = els.logContainer.scrollHeight;
  logCounter++;
  els.logCount.textContent = logCounter;
}

function addEvidence(source, content, isSuccess) {
  const el = document.createElement("div");
  el.className = `evidence-item ${!isSuccess ? "error-evidence" : ""}`;
  el.innerHTML = `<div class="evidence-type">${escapeHtml(source)}</div><div class="evidence-content">${escapeHtml(String(content))}</div>`;
  if (els.evidenceBoard.querySelector(".placeholder"))
    els.evidenceBoard.innerHTML = "";
  els.evidenceBoard.appendChild(el);
  evidenceCount++;
  updateStats();
}

function addMemory(text) {
  const el = document.createElement("div");
  el.className = "memory-item";
  el.textContent = text;
  if (els.taskMemory.querySelector(".placeholder"))
    els.taskMemory.innerHTML = "";
  els.taskMemory.appendChild(el);
}

function updateStats() {
  els.statSteps.textContent = stepCount;
  els.statSuccess.textContent = successCount;
  els.statFailed.textContent = failCount;
  els.statEvidence.textContent = evidenceCount;
}

function escapeHtml(str) {
  return String(str).replace(
    /[&<>'"]/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;" })[
        c
      ],
  );
}

init();

async function loadPendingConfirmations() {
  if (!els.pendingActionsList) return;
  try {
    const res = await fetch(`${API_BASE}/api/confirmations/pending`);
    const data = await res.json();
    const items = data.items || [];
    if (!items.length) {
      els.pendingActionsList.innerHTML =
        '<p class="placeholder">暂无待确认动作</p>';
      return;
    }
    els.pendingActionsList.innerHTML = items
      .map(
        (item) => `<div class="memory-item">
          <strong>${escapeHtml(item.skill || item.action)}</strong> · ${escapeHtml(item.risk_level)}<br>
          <span>${escapeHtml(item.reason || "")}</span><br>
          <button class="btn-secondary" onclick="approveConfirmation('${item.id}')">批准</button>
          <button class="btn-secondary" onclick="rejectConfirmation('${item.id}')">拒绝</button>
        </div>`,
      )
      .join("");
  } catch (e) {
    els.pendingActionsList.innerHTML = `<p class="placeholder">加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

async function approveConfirmation(id) {
  const res = await fetch(
    `${API_BASE}/api/confirmations/${id}/approve-execute`,
    {
      method: "POST",
    },
  );
  const data = await res.json();
  log(
    `已批准并原地执行 ${id}: ${(data.results || []).length} 个结果`,
    "success",
    "✅",
    new Date().toLocaleTimeString(),
  );
  if (data.resume_payload?.task_id) {
    await connectContractWebSocket(null, null, data.resume_payload.task_id);
  }
  await loadPendingConfirmations();
  await loadResumableTasks();
}

async function rejectConfirmation(id) {
  const reason =
    window.prompt(
      "拒绝原因（将交给 FailureHandler 重新规划）",
      "用户拒绝此动作",
    ) || "用户拒绝此动作";
  const res = await fetch(`${API_BASE}/api/confirmations/${id}/reject-repair`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ reason }),
  });
  const data = await res.json();
  log(
    `已拒绝 ${id}，插入 repair steps: ${(data.repair_steps_inserted || []).length}`,
    "warning",
    "❌",
    new Date().toLocaleTimeString(),
  );
  if (data.resume_payload?.task_id) {
    await connectContractWebSocket(null, null, data.resume_payload.task_id);
  }
  await loadPendingConfirmations();
  await loadResumableTasks();
}

async function loadResumableTasks() {
  if (!els.resumableTasksList) return;
  try {
    const res = await fetch(`${API_BASE}/api/tasks/resumable`);
    const data = await res.json();
    const tasks = data.tasks || [];
    if (!tasks.length) {
      els.resumableTasksList.innerHTML =
        '<p class="placeholder">暂无可恢复任务</p>';
      return;
    }
    els.resumableTasksList.innerHTML = tasks
      .map(
        (task) => `<div class="memory-item">
          <strong>${escapeHtml(task.task_id)}</strong><br>
          step: ${task.current_step_index}/${task.total_steps || 0} · completed: ${task.completed || 0} · failed: ${task.failed || 0}<br>
          <span>${escapeHtml(task.final_goal || "")}</span><br>
          <button class="btn-secondary" onclick="resumeTask('${task.task_id}')">恢复执行</button>
        </div>`,
      )
      .join("");
  } catch (e) {
    els.resumableTasksList.innerHTML = `<p class="placeholder">加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

async function loadRecentTasks() {
  if (!els.recentTasksList) return;
  try {
    const res = await fetch(`${API_BASE}/api/tasks`);
    const data = await res.json();
    const tasks = data.tasks || [];
    if (!tasks.length) {
      els.recentTasksList.innerHTML = '<p class="placeholder">暂无最近任务</p>';
      return;
    }
    els.recentTasksList.innerHTML = tasks
      .slice(0, 10)
      .map((task) => {
        const goal = task.goal_contract?.final_goal || task.user_input || "";
        const status = task.status || "unknown";
        const needsUser = status === "needs_user" || task.pending_external_ai;
        const productError = task.product_error || {};
        const taskId = task.task_id || task.id || "task";
        return `<div class="memory-item">
          <strong>${escapeHtml(goal || taskId)}</strong><br>
          <small>${escapeHtml(taskId)} · ${escapeHtml(taskStatusLabel(status))}</small><br>
          <small>项目：${escapeHtml(task.project_path || task.goal_contract?.project_path || "—")}</small><br>
          <small>阶段：${escapeHtml(task.phase || "—")} · 完成：${Number(task.current_step || 0)}/${Number(task.plan?.total_steps || 0)}</small><br>
          <small>Claude 调用：${Number(task.claude_call_count || 0)} · 修改文件：${Number((task.files_changed || []).length)}</small><br>
          <small>创建：${formatTaskTime(task.created_at)} · 更新：${formatTaskTime(task.updated_at)}</small><br>
          <small>工具调用：${Number(task.tool_call_count || 0)} · Evidence：${Number(task.evidence_count || 0)}</small><br>
          <span>${escapeHtml(goal)}</span><br>
          ${task.failure_reason ? `<small>失败原因：${escapeHtml(productError.message || productFailureLabel(task.failure_reason))}</small><br>` : ""}
          ${productError.next_action ? `<small>建议下一步：${escapeHtml(productError.next_action)}</small><br>` : ""}
          ${needsUser ? '<small class="warning-text">任务暂停，等待用户处理</small><br>' : ""}
          ${task.report_available ? `<button class="btn-secondary" onclick="viewTaskReport('${escapeHtml(taskId)}')">查看报告</button>` : ""}
          <button class="btn-secondary" onclick="viewTaskDetails('${escapeHtml(taskId)}')">查看计划与修改</button>
          ${task.rollback_available ? `<button class="btn-secondary" onclick="showTaskRollbackOptions('${escapeHtml(taskId)}')">回滚选项</button>` : ""}
          <button class="btn-secondary" onclick="openTaskDirectory('${escapeHtml(taskId)}')">打开任务目录</button>
          ${needsUser ? `<button class="btn-secondary" onclick="resumeTask('${escapeHtml(taskId)}')">继续任务</button>` : ""}
        </div>`;
      })
      .join("");
  } catch (e) {
    els.recentTasksList.innerHTML = `<p class="placeholder">加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

function formatTaskTime(value) {
  return value ? new Date(value).toLocaleString() : "—";
}

function taskStatusLabel(status) {
  const labels = {
    created: "正在准备",
    planned: "正在规划",
    running: "正在执行",
    success: "已完成",
    completed_unverified: "已完成，等待确认",
    failed: "已失败",
    paused: "已暂停",
    interrupted: "已中断，可恢复",
    rolled_back: "已回滚",
    needs_user: "需要用户处理",
    waiting_confirmation: "等待确认",
    verifying: "正在验证",
    repairing: "正在修复",
  };
  return labels[status] || status;
}

function productFailureLabel(reason) {
  const labels = {
    local_model_unavailable: "本地模型未连接",
    local_model_error: "本地模型暂时不可用",
    project_path_not_found: "项目路径不存在",
    write_confirmation_required: "等待确认文件修改权限",
    playwright_browser_missing: "项目专用浏览器未安装",
    claude_login_required: "Claude 需要登录",
    verification_failed: "项目验证未通过",
    command_failed: "命令执行失败",
    unsupported_repair: "自动修复暂不支持",
    permission_denied: "权限不足",
    task_resume_failed: "任务恢复失败",
    simulated_app_close: "任务已中断，可恢复",
  };
  return labels[String(reason || "").toLowerCase()] || String(reason || "未知错误");
}

async function openTaskDirectory(taskId) {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}/open`, { method: "POST" });
  const data = await res.json();
  log(
    data.opened ? `已打开任务目录：${taskId}` : `无法打开任务目录：${data.error || "unknown"}`,
    data.opened ? "success" : "error",
    data.opened ? "✓" : "!",
    new Date().toLocaleTimeString(),
  );
}

async function viewTaskReport(taskId) {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}/report`);
  const report = await res.text();
  if (!res.ok) {
    log(`报告加载失败: ${report}`, "error", "❌", new Date().toLocaleTimeString());
    return;
  }
  els.reportArea.style.display = "block";
  els.reportContent.textContent = report;
  log(`已打开任务报告: ${taskId}`, "info", "📝", new Date().toLocaleTimeString());
}

async function viewTaskDetails(taskId) {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}`);
  const data = await res.json();
  const task = data.task || {};
  const contract = task.goal_contract || {};
  const plan = task.plan?.plan || [];
  els.reportArea.style.display = "block";
  els.reportContent.textContent = [
    "Goal Contract",
    `目标：${contract.user_goal || contract.final_goal || "—"}`,
    `成功标准：${(contract.success_criteria || []).join("；") || "—"}`,
    `禁止动作：${(contract.forbidden_actions || []).join("；") || "—"}`,
    "",
    "执行计划",
    ...plan.map((step) => `${step.step_id || step.step || "step"} · ${step.objective || step.goal || ""} · ${step.status || "pending"} · 验证：${step.verification || step.verification_method || "—"}`),
    "",
    `修改文件：${(task.files_changed || []).join("、") || "无"}`,
    `失败原因：${task.failure_reason || "无"}`,
  ].join("\n");
}

async function rollbackLatestTaskCheckpoint(taskId) {
  if (!confirm("确认回滚这个隔离任务副本的最近修改？不会修改任务目录外的其他项目。")) return;
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}/rollback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ checkpoint_id: "" }),
  });
  const data = await res.json();
  log(data.success ? `任务 ${taskId} 已回滚` : `回滚失败：${data.failure_reason || "unknown"}`, data.success ? "success" : "error", data.success ? "↩" : "!", new Date().toLocaleTimeString());
  await loadRecentTasks();
}

async function showTaskRollbackOptions(taskId) {
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}/checkpoints`);
  const data = await res.json();
  const checkpoints = data.checkpoints || [];
  els.reportArea.style.display = "block";
  els.reportContent.innerHTML = `<strong>可回滚点</strong><br>
    <small>回滚只影响这个任务配置的项目副本。回滚后应重新运行验证。</small><br><br>
    ${checkpoints.map((item, index) => `<button class="btn-secondary" onclick="rollbackTaskCheckpoint('${escapeHtml(taskId)}','${escapeHtml(item.checkpoint_id)}')">${index === 0 ? "回滚整个任务" : "回滚到最后成功 checkpoint"} · ${escapeHtml(item.reason)}</button>`).join(" ")}`;
}

async function rollbackTaskCheckpoint(taskId, checkpointId) {
  if (!confirm("确认回滚这个隔离任务副本？不会修改任务目录外的项目。")) return;
  const res = await fetch(`${API_BASE}/api/tasks/${taskId}/rollback`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ checkpoint_id: checkpointId }),
  });
  const data = await res.json();
  log(
    data.success ? `已回滚到 ${checkpointId}，请重新验证项目` : `回滚失败：${data.failure_reason || "unknown"}`,
    data.success ? "success" : "error",
    data.success ? "↩" : "!",
    new Date().toLocaleTimeString(),
  );
  await loadRecentTasks();
}

async function resumeTask(taskId) {
  log(`恢复任务 ${taskId}`, "phase", "🔁", new Date().toLocaleTimeString());
  resetUi();
  try {
    const detailRes = await fetch(`${API_BASE}/api/tasks/${taskId}`);
    const detail = await detailRes.json();
    const task = detail.task || {};
    if (task.project_path && task.status === "interrupted") {
      const res = await fetch(`${API_BASE}/api/tasks/${taskId}/resume-real-project-async`, {
        method: "POST",
      });
      const result = await res.json();
      currentTaskId = taskId;
      renderRealProjectGoalContract(task.goal_contract || {});
      renderRealProjectPlan(task.plan || {});
      log(`真实项目任务 ${taskId} 正在恢复，继续接收实时事件`, "phase", "↻", new Date().toLocaleTimeString());
      taskSubmissionInFlight = true;
      connectRealProjectEvents(taskId, Number(result.after_event_id || 0));
      return;
    }
    await connectContractWebSocket(null, null, taskId);
  } finally {
    finishUi();
  }
}

async function loadWebAiProfiles() {
  try {
    const res = await fetch(`${API_BASE}/api/web-ai/profiles/status`);
    const data = await res.json();
    const profiles = data.profiles || {};
    const container = document.getElementById("aiProfiles");
    if (!container) return;
    const providers = ["claude", "chatgpt"];
    let html = '<div style="display:flex;flex-direction:column;gap:6px;">';
    for (const provider of providers) {
      const p = profiles[provider] || {
        test_status: "not_run",
        logged_in: false,
        initialized: false,
      };
      const state = providerProductState(provider, p);
      const dotClass =
        ["TEST_PASS", "READY", "TEST_PARTIAL"].includes(state)
          ? "available"
          : "unavailable";
      const testedLabel = p.test_summary?.created_at
        ? new Date(p.test_summary.created_at).toLocaleDateString()
        : "—";
      const recommendation = p.recommendation_label || (
        provider === "claude" && state === "TEST_PASS"
          ? "推荐使用"
          : provider === "chatgpt" && state === "TEST_PARTIAL"
          ? "可用但不稳定"
          : p.test_status === "FAIL"
          ? "需要重新测试"
          : "");
      html += `<div class="ai-profile-item" style="flex-direction:column;align-items:flex-start;gap:2px;">
        <div class="ai-profile-dot ${dotClass}"></div>
        <span><strong>${provider === "claude" ? "Claude Web" : "ChatGPT Web"}</strong>${recommendation ? ` <span class="ai-profile-badge">${escapeHtml(recommendation)}</span>` : ""}</span>
        <small>${escapeHtml(providerStateLabel(state))} · 最近测试：${testedLabel}</small>
        <small>${escapeHtml(providerGuidance(provider, state))}</small>
        <div style="display:flex;gap:4px;margin-top:2px;">
          <button class="btn-secondary" data-workspace-open="${provider}" onclick="openWebAiWorkspace('${provider}', this)" style="font-size:10px;padding:2px 6px;">打开工作区</button>
          <button class="btn-secondary" onclick="refreshWorkspaceStatus('${provider}')" style="font-size:10px;padding:2px 6px;">重新检测</button>
        </div>
      </div>`;
    }
    html += '<details class="inactive-providers"><summary>未启用 provider</summary><small>豆包、Kimi、Gemini 暂未启用，不影响基础本地任务。</small></details>';
    html += "</div>";
    container.innerHTML = html;
  } catch (e) {
    /* non-critical */
  }
}

function providerProductState(provider, profile) {
  if (profile.test_status === "PASS") return "TEST_PASS";
  if (profile.test_status === "PASS_WITH_WARNING") return "TEST_PASS_WARNING";
  if (profile.test_status === "PARTIAL") return "TEST_PARTIAL";
  if (profile.workspace_state === "NEED_USER_INTERVENTION") return "NEED_USER_INTERVENTION";
  if (profile.workspace_state === "READY") return "READY";
  if (profile.has_profile_dir || profile.workspace_state === "NEED_LOGIN") return "NEED_LOGIN";
  return "NOT_CONFIGURED";
}

function providerStateLabel(state) {
  const labels = {
    NOT_CONFIGURED: "未配置",
    INSTALL_REQUIRED: "需要安装",
    DISCONNECTED: "未连接",
    NEED_LOGIN: "需要登录",
    NEED_LOCAL_SERVICE: "需要启动本地服务",
    NEED_MODEL: "需要加载模型",
    ACCOUNT_RESTRICTED: "账号权限受限",
    REGION_RESTRICTED: "地区受限",
    CAPTCHA_REQUIRED: "需要人工验证码",
    PROVIDER_CHANGED: "页面结构已变化",
    FAILED_PRODUCT_BUG: "产品故障",
    DISABLED_BY_USER: "用户已停用",
    READY: "可用",
    BUSY: "正在使用",
    DEGRADED: "部分可用",
    PARTIAL: "部分可用",
    ERROR: "连接错误",
    FAIL: "连接错误",
    DISABLED: "已停用",
    PASS: "已验证",
    TEST_PASS: "测试通过",
    TEST_PASS_WARNING: "成功，附带警告",
    TEST_PARTIAL: "可用但不稳定",
    NEED_USER_INTERVENTION: "需要你处理",
    local_first: "本地优先",
    fully_local: "完全本地",
    manual_confirmation: "手动确认",
    best_capability: "最佳能力",
  };
  return labels[state] || state;
}

function providerGuidance(provider, state) {
  if (provider === "claude" && state === "NEED_LOGIN") return "Claude 未登录，点击打开工作区。";
  if (provider === "claude" && ["READY", "TEST_PASS", "TEST_PASS_WARNING"].includes(state)) return "Claude 已可用。";
  if (provider === "chatgpt" && state === "NOT_CONFIGURED") return "ChatGPT 未配置，仅作为后续 fallback。";
  return "外部 AI 可选，不影响基础本地任务。";
}

function boolMark(value) {
  return value ? "✓" : "—";
}

async function loadWebAiMatrix() {
  if (!els.webAiMatrix) return;
  try {
    const res = await fetch(`${API_BASE}/api/web-ai/test-matrix`);
    const data = await res.json();
    const allProviders = data.providers || [];
    const providers = allProviders;
    const inactive = [];
    if (!providers.length) {
      els.webAiMatrix.innerHTML = '<p class="placeholder">暂无 provider 测试报告</p>';
      return;
    }
    els.webAiMatrix.innerHTML = `<table class="matrix-table">
      <thead>
        <tr>
          <th>Provider</th><th>Login</th><th>Send</th><th>Wait</th><th>Extract</th><th>AQ</th><th>Status</th><th>Last</th><th>Evidence</th>
        </tr>
      </thead>
      <tbody>
        ${providers.map((p) => `<tr onclick='showWebAiMatrixDetail(${JSON.stringify(p).replace(/'/g, "&#39;")})'>
          <td>${escapeHtml(p.provider)}</td>
          <td>${boolMark(p.login)}</td>
          <td>${boolMark(p.send)}</td>
          <td>${boolMark(p.wait)}</td>
          <td>${boolMark(p.extract)}</td>
          <td>${escapeHtml(p.aq || "NOT_RUN")}</td>
          <td>${escapeHtml(p.state || p.status || "NOT_CONFIGURED")}</td>
          <td>${escapeHtml(p.last_tested ? new Date(p.last_tested).toLocaleDateString() : "—")}</td>
          <td>${p.evidence_path ? "✓" : "—"}</td>
        </tr>`).join("")}
      </tbody>
    </table>
    ${inactive.length ? `<details class="inactive-providers"><summary>未启用 provider</summary><small>${inactive.map((p) => escapeHtml(p.provider)).join("、")} 暂未启用，不会自动测试。</small></details>` : ""}`;
  } catch (e) {
    els.webAiMatrix.innerHTML = `<p class="placeholder">矩阵加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

function showWebAiMatrixDetail(p) {
  if (!els.webAiMatrixDetail) return;
  els.webAiMatrixDetail.classList.remove("hidden");
  els.webAiMatrixDetail.innerHTML = `<strong>${escapeHtml(p.provider)}</strong>
    <div>failure reason: ${escapeHtml(p.failure_reason || "—")}</div>
    <div>used_selector: ${escapeHtml(p.used_selector || "—")}</div>
    <div>quality_issues: ${escapeHtml((p.quality_issues || []).join("; ") || "—")}</div>
    <div>evidence: ${escapeHtml(p.evidence_path || "—")}</div>
    <div>screenshot: ${escapeHtml(p.screenshot_path || "—")}</div>
    <div>metadata: ${escapeHtml(p.metadata_path || "—")}</div>`;
}

async function loadPlaywrightStatus() {
  if (!els.playwrightStatus) return;
  try {
    const res = await fetch(`${API_BASE}/api/playwright/status`);
    const data = await res.json();
    latestPlaywrightStatus = data;
    const ready = data.exists && data.chromium_found;
    const statusText = ready ? "可用" : "需要安装项目专用浏览器";
    const actionText = ready ? "ready" : "项目专用浏览器未安装。外部 AI 网页控制可能不可用。";
    els.playwrightStatus.innerHTML = `<div class="memory-item">
      <strong>${escapeHtml(statusText)}</strong><br>
      path: ${escapeHtml(data.configured_path || "—")}<br>
      exists: ${data.exists ? "yes" : "no"} · chromium: ${data.chromium_found ? "yes" : "no"}<br>
      <span class="${ready ? "success-text" : "warning-text"}">${escapeHtml(data.recommended_action || actionText)}</span><br>
      ${data.install_state?.state === "running" ? `<span class="warning-text">正在下载项目专用浏览器…</span>
      <button class="btn-secondary" onclick="cancelProjectBrowserInstall()">取消下载</button>` : ""}
      ${ready ? "" : `<button class="btn-secondary" onclick="showPlaywrightInstallHelp()">查看安装说明</button>
      <button class="btn-secondary" onclick="installProjectBrowser()">安装项目专用浏览器</button>
      <button class="btn-secondary" onclick="dismissPlaywrightNotice()">暂不安装</button>`}
    </div>`;
    renderFirstRunStatus();
  } catch (e) {
    els.playwrightStatus.innerHTML = `<p class="placeholder">Playwright 状态加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

async function installProjectBrowser() {
  const preview = await fetch(`${API_BASE}/api/playwright/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: false }),
  }).then((res) => res.json());
  if (!confirm(`确认下载项目专用 Chromium？\n预计大小：${preview.estimated_download_size}\n只写入 App data / 项目专用目录，不使用系统缓存。`)) return;
  const started = await fetch(`${API_BASE}/api/playwright/install`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  }).then((res) => res.json());
  log(started.started ? "项目专用浏览器开始下载，可在日志中查看进度" : "浏览器安装任务已经在运行", "info", "↓", new Date().toLocaleTimeString());
  await loadPlaywrightStatus();
  pollProjectBrowserInstall();
}

async function cancelProjectBrowserInstall() {
  await fetch(`${API_BASE}/api/playwright/install/cancel`, { method: "POST" });
  log("已请求取消项目专用浏览器下载", "warning", "!", new Date().toLocaleTimeString());
  await loadPlaywrightStatus();
}

async function pollProjectBrowserInstall() {
  for (let index = 0; index < 120; index += 1) {
    await new Promise((resolve) => setTimeout(resolve, 2000));
    const data = await fetch(`${API_BASE}/api/playwright/status`).then((res) => res.json());
    latestPlaywrightStatus = data;
    await loadPlaywrightStatus();
    if (data.install_state?.state !== "running") {
      log(data.chromium_found ? "项目专用浏览器安装完成" : `浏览器安装未完成：${data.install_state?.failure_reason || "unknown"}`, data.chromium_found ? "success" : "warning", data.chromium_found ? "✓" : "!", new Date().toLocaleTimeString());
      break;
    }
  }
}

const providerNames = {
  lmstudio: "LM Studio",
  ollama: "Ollama",
  claude: "Claude Web",
  chatgpt: "ChatGPT Web",
  gemini: "Gemini Web",
  kimi: "Kimi Web",
  doubao: "豆包 Web",
};

function allProviders(data = latestProviderOverview) {
  return [...(data?.local || []), ...(data?.web || [])];
}

function renderProviderSummary(data) {
  const providers = allProviders(data);
  const enabled = providers.filter((provider) => provider.enabled);
  const verified = providers.filter((provider) => provider.acceptance_status === "VERIFIED");
  const routing = data.routing || {};
  const defaultExternal = (routing.priority || []).find((name) => data.web?.find((provider) => provider.provider === name)?.route_eligible) || "尚无已验证网页 AI";
  if (els.providerEnabledCount) els.providerEnabledCount.textContent = String(enabled.length);
  if (els.providerVerifiedCount) els.providerVerifiedCount.textContent = String(verified.length);
  if (els.providerDefaultLocal) els.providerDefaultLocal.textContent = providerNames[data.local_model_routing?.default_provider] || data.local_model_routing?.default_provider || "—";
  if (els.providerDefaultExternal) els.providerDefaultExternal.textContent = providerNames[defaultExternal] || defaultExternal;
  if (els.taskProviderSummary) {
    els.taskProviderSummary.innerHTML = `<div class="memory-item"><strong>本地模型</strong><br>${escapeHtml(providerNames[data.local_model_routing?.default_provider] || "规则规划")} · ${escapeHtml(providerStateLabel(data.local?.find((provider) => provider.provider === data.local_model_routing?.default_provider)?.state || "NOT_CONFIGURED"))}</div>
      <div class="memory-item"><strong>外部 AI</strong><br>${escapeHtml(providerNames[defaultExternal] || defaultExternal)}</div>
      <div class="memory-item"><strong>路由模式</strong><br>${escapeHtml(providerStateLabel(routing.routing_policy) || routing.routing_policy || "本地优先")}</div>`;
  }
}

function renderProviderChoices(data) {
  if (!els.providerChoiceGrid) return;
  els.providerChoiceGrid.innerHTML = allProviders(data).map((provider) => `<label class="provider-choice">
    <strong>${escapeHtml(providerNames[provider.provider] || provider.provider)}</strong>
    <small>${provider.kind === "local" ? "本地模型" : "网页 AI"} · ${escapeHtml(providerStateLabel(provider.acceptance_status || provider.state))}</small>
    <select data-provider-choice="${provider.provider}">
      <option value="enabled" ${provider.onboarding_choice === "enabled" || provider.enabled ? "selected" : ""}>启用</option>
      <option value="skipped" ${provider.onboarding_choice === "skipped" ? "selected" : ""}>暂不使用</option>
      <option value="later" ${provider.onboarding_choice === "later" ? "selected" : ""}>稍后配置</option>
    </select>
  </label>`).join("");
}

function renderProviderPriority(priority) {
  if (!els.providerPriorityList) return;
  els.providerPriorityList.innerHTML = priority.map((provider, index) => `<div class="provider-priority-item"><span>${index + 1}. ${escapeHtml(providerNames[provider] || provider)}</span><span><button class="btn-secondary" title="上移" onclick="moveProviderPriority('${provider}', -1)">↑</button><button class="btn-secondary" title="下移" onclick="moveProviderPriority('${provider}', 1)">↓</button></span></div>`).join("");
}

function moveProviderPriority(provider, direction) {
  const priority = (els.providerPriority?.value || "").split(",").map((item) => item.trim()).filter(Boolean);
  const index = priority.indexOf(provider);
  const target = index + direction;
  if (index < 0 || target < 0 || target >= priority.length) return;
  [priority[index], priority[target]] = [priority[target], priority[index]];
  els.providerPriority.value = priority.join(", ");
  renderProviderPriority(priority);
}

function startProviderOnboarding() {
  providerWizardIndex = 0;
  els.providerOnboardingWizard?.classList.remove("hidden");
  renderProviderWizardStep();
}

function stopProviderOnboarding() {
  els.providerOnboardingWizard?.classList.add("hidden");
}

async function saveProviderChoices() {
  const choices = {};
  document.querySelectorAll("[data-provider-choice]").forEach((select) => {
    choices[select.dataset.providerChoice] = select.value;
  });
  await fetch(`${API_BASE}/api/providers/onboarding`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ choices }) });
  log("AI 服务选择已保存", "success", "✓", new Date().toLocaleTimeString());
  await loadProviderServices();
  renderProviderWizardStep();
}

function renderProviderWizardStep() {
  if (!els.providerWizardStep) return;
  const providerName = providerWizardOrder[providerWizardIndex];
  if (!providerName) {
    els.providerWizardProgress.textContent = "配置向导已完成。失败或外部限制不会阻塞其他服务。";
    els.providerWizardStep.innerHTML = '<strong>配置完成</strong><p>可以关闭向导并开始使用。只有已验证服务会参与自动路由。</p>';
    return;
  }
  const provider = allProviders().find((item) => item.provider === providerName) || {};
  const enabled = provider.enabled;
  els.providerWizardProgress.textContent = `第 ${providerWizardIndex + 1} / ${providerWizardOrder.length} 项`;
  if (!enabled) {
    els.providerWizardStep.innerHTML = `<strong>${escapeHtml(providerNames[providerName])}</strong><p>当前未启用。可以跳过，或在上方选择“启用”后保存选择。</p>`;
    return;
  }
  if (provider.kind === "local") {
    els.providerWizardStep.innerHTML = `<strong>${escapeHtml(providerNames[providerName])}</strong><p>状态：${escapeHtml(providerStateLabel(provider.state))} · 模型：${escapeHtml(provider.default_model || "未选择")}</p><div class="provider-card-actions"><button class="btn-secondary" onclick="detectProvider('${providerName}')">自动检测</button><button class="btn-secondary" onclick="testLocalProvider('${providerName}').then(providerWizardNext)">测试并继续</button></div>`;
    return;
  }
  els.providerWizardStep.innerHTML = `<strong>${escapeHtml(providerNames[providerName])}</strong><p>状态：${escapeHtml(providerStateLabel(provider.acceptance_status || provider.state))}</p><p>请在项目专用工作区手动完成登录或验证，然后点击“我已登录，检测并测试”。每个平台最多发送一次 minimal prompt。</p><div class="provider-card-actions"><button class="btn-secondary" data-workspace-open="${providerName}" onclick="openWebAiWorkspace('${providerName}', this)">打开工作区</button><button class="btn-secondary" onclick="refreshWorkspaceStatus('${providerName}')">重新检测</button><button class="btn-secondary" onclick="wizardVerifyWebProvider('${providerName}')">我已登录，检测并测试</button></div>`;
}

function providerWizardNext() {
  providerWizardIndex += 1;
  renderProviderWizardStep();
}

async function wizardVerifyWebProvider(provider) {
  const status = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/status`).then((res) => res.json());
  renderWorkspaceStatus(status);
  if (!["READY", "PASS", "PARTIAL"].includes(status.state || status.workspace_state)) {
    log(`${providerNames[provider]} 仍需用户处理，向导保留在当前项`, "warning", "!", new Date().toLocaleTimeString());
    return;
  }
  await runProviderLiveMinimal(provider);
  providerWizardNext();
}

async function runProviderLiveMinimal(provider) {
  const data = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/live-minimal`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ confirmed: true }) }).then((res) => res.json());
  const quality = data.answer_quality?.quality || "";
  log(`${providerNames[provider]} 验收：${data.success ? quality || "已验证" : data.failure_reason || "需要用户处理"}`, data.success ? "success" : "warning", data.success ? "✓" : "!", new Date().toLocaleTimeString());
  await loadProviderServices();
  return data;
}

async function loadProviderServices() {
  if (!els.localProviderCards || !els.webProviderCards) return;
  try {
    const data = await fetch(`${API_BASE}/api/providers`).then((res) => res.json());
    latestProviderOverview = data;
    const routing = data.routing || {};
    els.providerRoutingPolicy.value = routing.routing_policy || "local_first";
    els.providerAllowAutomatic.checked = Boolean(routing.allow_automatic);
    els.providerRequireConfirmation.checked = routing.require_confirmation !== false;
    els.providerMaxCalls.value = Number(routing.max_calls_per_task || 1);
    if (els.providerPriority) els.providerPriority.value = (routing.priority || ["claude", "chatgpt", "gemini", "kimi", "doubao"]).join(", ");
    renderProviderPriority(routing.priority || ["claude", "chatgpt", "gemini", "kimi", "doubao"]);
    if (els.localModelSimpleMode) els.localModelSimpleMode.checked = data.local_model_routing?.simple_mode !== false;
    renderLocalModelRoleSettings(data);
    const enabledLocal = (data.local || []).filter((provider) => provider.enabled);
    const disabledLocal = (data.local || []).filter((provider) => !provider.enabled);
    els.localProviderCards.innerHTML = enabledLocal.map(renderLocalProviderCard).join("");
    const enabled = (data.web || []).filter((provider) => provider.enabled);
    const disabled = [...disabledLocal, ...(data.web || []).filter((provider) => !provider.enabled)];
    els.webProviderCards.innerHTML = enabled.length ? enabled.map(renderWebProviderCard).join("") : '<p class="placeholder">尚未启用网页 AI。基础任务仍可使用本地模型或规则规划。</p>';
    if (els.disabledWebProviderCards) els.disabledWebProviderCards.innerHTML = disabled.map((provider) => provider.kind === "local" ? renderLocalProviderCard(provider) : renderWebProviderCard(provider)).join("");
    renderProductProviderMatrix(data.web || []);
    renderProviderSummary(data);
    renderProviderChoices(data);
  } catch (error) {
    els.localProviderCards.innerHTML = `<p class="placeholder">本地模型加载失败：${escapeHtml(error.message)}</p>`;
  }
}

function renderLocalProviderCard(provider) {
  const models = provider.models || [];
  return `<article class="provider-card" data-provider-card="${provider.provider}">
    <header class="provider-card-header"><div><h4>${escapeHtml(providerNames[provider.provider] || provider.provider)}</h4><small>本地模型 · ${escapeHtml(providerStateLabel(provider.acceptance_status || provider.state))}</small></div><span class="provider-state">${provider.enabled ? "已启用" : "未启用"}</span></header>
    <label><input id="${provider.provider}Enabled" type="checkbox" ${provider.enabled ? "checked" : ""}> 启用</label>
    <label>默认模型<select id="${provider.provider}Model"><option value="">请选择模型</option>${models.map((model) => `<option value="${escapeHtml(model)}" ${model === provider.default_model ? "selected" : ""}>${escapeHtml(model)}</option>`).join("")}</select></label>
    <small>当前模型：${escapeHtml(provider.default_model || "未选择")} · 最近检测：${Number(provider.latency_ms || 0)} ms</small><br>
    ${provider.failure_reason ? `<small class="warning-text">错误：${escapeHtml(provider.failure_reason)}</small>` : ""}
    <div class="provider-card-actions">
      <button class="btn-secondary" onclick="detectProvider('${provider.provider}')">自动检测</button>
      <button class="btn-secondary" onclick="testLocalProvider('${provider.provider}')">测试</button>
      <button class="btn-secondary" onclick="saveLocalProvider('${provider.provider}')">保存设置</button>
    </div>
    <details><summary>高级信息</summary>
      <label>Endpoint<input id="${provider.provider}Endpoint" value="${escapeHtml(provider.endpoint || "")}"></label>
      <label>超时（秒）<input id="${provider.provider}Timeout" type="number" min="1" max="600" value="${Number(provider.timeout_seconds || 120)}"></label>
      <label>最大上下文<input id="${provider.provider}Context" type="number" min="1024" value="${Number(provider.max_context || 32768)}"></label>
      <label>温度<input id="${provider.provider}Temperature" type="number" min="0" max="2" step="0.1" value="${Number(provider.temperature ?? 0.3)}"></label>
      <label>最大 token<input id="${provider.provider}MaxTokens" type="number" min="1" value="${Number(provider.max_tokens || 4096)}"></label>
      <button class="btn-secondary" onclick="testLocalProviderRoles('${provider.provider}')">测试模型角色</button>
      <button class="btn-secondary" onclick="showProviderDiagnostics('${provider.provider}')">查看错误</button>
    </details>
  </article>`;
}

function renderWebProviderCard(provider) {
  return `<article class="provider-card" data-provider-card="${provider.provider}">
    <header class="provider-card-header"><div><h4>${escapeHtml(providerNames[provider.provider] || provider.provider)}</h4><small>网页 AI · ${escapeHtml(providerStateLabel(provider.acceptance_status || provider.state))}</small></div><span class="provider-state">${escapeHtml(provider.routing_role === "default" ? "默认" : provider.enabled ? "备用" : "禁用")}</span></header>
    <label><input id="${provider.provider}Enabled" type="checkbox" ${provider.enabled ? "checked" : ""}> 启用这个 Provider</label>
    <small>当前模型：${escapeHtml(provider.default_model || "由网页工作区选择")}<br>最近结果：${escapeHtml(provider.last_result || "未验证")} · 最近测试：${escapeHtml(provider.last_tested || "—")}<br>自动路由：${provider.route_eligible ? "可参与" : "不可参与"}</small>
    <div class="provider-card-actions">
      <button class="btn-secondary" data-workspace-open="${provider.provider}" onclick="openWebAiWorkspace('${provider.provider}', this)">打开工作区</button>
      <button class="btn-secondary" onclick="refreshWorkspaceStatus('${provider.provider}')">重新检测</button>
      <button class="btn-secondary" onclick="runProviderLiveMinimal('${provider.provider}')">测试</button>
      <button class="btn-secondary" onclick="saveWebProvider('${provider.provider}')">保存启用状态</button>
    </div>
    <details><summary>高级信息</summary><button class="btn-secondary" onclick="closeWebAiWorkspace('${provider.provider}')">关闭工作区</button><button class="btn-secondary" onclick="showWebAiEvidence('${provider.provider}')">查看 evidence</button><button class="btn-secondary" onclick="resetWebAiProfile('${provider.provider}')">重置 profile</button></details>
  </article>`;
}

function renderProductProviderMatrix(providers) {
  if (!els.productProviderMatrix) return;
  els.productProviderMatrix.innerHTML = `<table class="matrix-table"><thead><tr><th>Provider</th><th>登录</th><th>发送</th><th>等待</th><th>提取</th><th>新对话</th><th>会话保持</th><th>模型选择</th><th>Evidence</th><th>Pending/Resume</th><th>Agent 联合</th></tr></thead><tbody>
    ${providers.map((provider) => {
      const capability = provider.capabilities || {};
      const label = (value) => value === true ? "已验证" : value === "NOT_VERIFIED" ? "未验证" : value ? "部分验证" : "未验证";
      return `<tr><td>${escapeHtml(providerNames[provider.provider] || provider.provider)}</td><td>${provider.needs_login ? "需要用户操作" : label(capability.login)}</td><td>${label(capability.send)}</td><td>${label(capability.wait)}</td><td>${label(capability.extract)}</td><td>${label(capability.new_conversation)}</td><td>${label(capability.session_persistence)}</td><td>${label(capability.model_selection)}</td><td>${label(capability.evidence)}</td><td>${label(capability.pending_resume)}</td><td>${label(capability.agent_joint_task)}</td></tr>`;
    }).join("")}</tbody></table>`;
}

async function detectProvider(provider) {
  const data = await fetch(`${API_BASE}/api/providers/${provider}/detect`).then((res) => res.json());
  log(`${providerNames[provider] || provider}：${providerStateLabel(data.state)}${data.failure_reason ? ` · ${data.failure_reason}` : ""}`, data.state === "READY" ? "success" : "warning", "•", new Date().toLocaleTimeString());
  await loadProviderServices();
}

async function testLocalProvider(provider) {
  const model = document.getElementById(`${provider}Model`)?.value || "";
  const data = await fetch(`${API_BASE}/api/providers/${provider}/test`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ model }) }).then((res) => res.json());
  log(`${providerNames[provider]} 对话测试：${data.chat_success ? "成功" : `失败 · ${data.failure_reason || "unknown"}`}`, data.chat_success ? "success" : "warning", data.chat_success ? "✓" : "!", new Date().toLocaleTimeString());
}

async function testLocalProviderRoles(provider) {
  const data = await fetch(`${API_BASE}/api/providers/${provider}/role-test`, { method: "POST" }).then((res) => res.json());
  const passed = Object.values(data.roles || {}).filter((item) => item.success).length;
  log(`${providerNames[provider]} 角色测试：${passed}/5 通过`, data.success ? "success" : "warning", data.success ? "✓" : "!", new Date().toLocaleTimeString());
}

async function saveLocalProvider(provider) {
  const payload = {
    enabled: document.getElementById(`${provider}Enabled`)?.checked,
    endpoint: document.getElementById(`${provider}Endpoint`)?.value || "",
    default_model: document.getElementById(`${provider}Model`)?.value || "",
    timeout_seconds: Number(document.getElementById(`${provider}Timeout`)?.value || 120),
    max_context: Number(document.getElementById(`${provider}Context`)?.value || 32768),
    temperature: Number(document.getElementById(`${provider}Temperature`)?.value ?? 0.3),
    max_tokens: Number(document.getElementById(`${provider}MaxTokens`)?.value || 4096),
  };
  await fetch(`${API_BASE}/api/providers/${provider}/configure`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  log(`${providerNames[provider]} 设置已保存`, "success", "✓", new Date().toLocaleTimeString());
  await loadProviderServices();
}

function renderLocalModelRoleSettings(data) {
  if (!els.localModelRoleSettings) return;
  const routing = data.local_model_routing || {};
  const models = (data.local || []).flatMap((provider) => (provider.models || []).map((model) => `${provider.provider}:${model}`));
  const roles = ["planner", "executor", "repair", "verifier", "summarizer"];
  els.localModelRoleSettings.innerHTML = roles.map((role) => `<label>${role}<select id="localRole-${role}"><option value="">使用默认模型 / 规则 fallback</option>${models.map((model) => `<option value="${escapeHtml(model)}" ${routing.roles?.[role] === model ? "selected" : ""}>${escapeHtml(model)}</option>`).join("")}</select></label>`).join("");
}

async function saveLocalModelRouting() {
  const roles = {};
  for (const role of ["planner", "executor", "repair", "verifier", "summarizer"]) roles[role] = document.getElementById(`localRole-${role}`)?.value || "";
  await fetch(`${API_BASE}/api/providers/local-model-routing`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ simple_mode: els.localModelSimpleMode?.checked !== false, roles }) });
  log("本地模型角色设置已保存", "success", "✓", new Date().toLocaleTimeString());
}

async function showProviderDiagnostics(provider) {
  const data = await fetch(`${API_BASE}/api/providers/${provider}/diagnostics`).then((res) => res.json());
  log(`${providerNames[provider]}：${providerStateLabel(data.state)} · ${data.failure_reason || "无错误"}`, data.failure_reason ? "warning" : "success", "•", new Date().toLocaleTimeString());
}

async function showWebAiEvidence(provider) {
  const data = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/evidence`).then((res) => res.json());
  log(`${providerNames[provider]} evidence：${data.latest || data.evidence_path || "暂无"}`, "info", "•", new Date().toLocaleTimeString());
}

async function saveWebProvider(provider) {
  await fetch(`${API_BASE}/api/providers/${provider}/configure`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ enabled: document.getElementById(`${provider}Enabled`)?.checked }) });
  log(`${providerNames[provider]} 启用状态已保存`, "success", "✓", new Date().toLocaleTimeString());
  await loadProviderServices();
}

async function saveProviderRouting() {
  const priority = (els.providerPriority?.value || "").split(",").map((item) => item.trim().toLowerCase()).filter((item) => ["claude", "chatgpt", "gemini", "kimi", "doubao"].includes(item));
  const payload = { routing_policy: els.providerRoutingPolicy.value, allow_automatic: els.providerAllowAutomatic.checked, require_confirmation: els.providerRequireConfirmation.checked, max_calls_per_task: Number(els.providerMaxCalls.value || 1), priority: [...new Set(priority)] };
  await fetch(`${API_BASE}/api/providers/routing`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
  log("Provider 路由设置已保存", "success", "✓", new Date().toLocaleTimeString());
}

function workspaceOpenButtons(provider) {
  return [...document.querySelectorAll(`[data-workspace-open="${provider}"]`)];
}

function setWorkspaceOpenLoading(provider, loading) {
  for (const button of workspaceOpenButtons(provider)) {
    button.disabled = loading;
    button.textContent = loading ? "正在打开…" : button.dataset.defaultLabel || "打开工作区";
  }
}

function newWorkspaceRequestId(provider) {
  if (window.crypto?.randomUUID) return `${provider}-${window.crypto.randomUUID()}`;
  return `${provider}-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

async function openWebAiWorkspace(provider, sourceButton = null) {
  if (workspaceOpenRequests.has(provider)) {
    return workspaceOpenRequests.get(provider);
  }
  if (sourceButton && !sourceButton.dataset.defaultLabel) {
    sourceButton.dataset.defaultLabel = sourceButton.textContent.trim();
  }
  const requestId = newWorkspaceRequestId(provider);
  log(`打开 ${provider} 项目专用工作区… request=${requestId}`, "phase", "🌐", new Date().toLocaleTimeString());
  setWorkspaceOpenLoading(provider, true);
  const request = (async () => {
    try {
      const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/open`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ request_id: requestId }),
      });
      const data = await res.json();
      renderWorkspaceStatus(data);
      if (data.failure_code) {
        log(workspaceFailureLabel(data.failure_code, data.failure_reason), "error", "⚠", new Date().toLocaleTimeString());
      } else {
        log(`${providerNames[provider] || provider} 工作区状态：${data.workspace_state || data.state}（已打开则聚焦已有窗口）`, "success", "✓", new Date().toLocaleTimeString());
      }
      await loadProviderWorkspaceConsole();
      return data;
    } catch (error) {
      const data = {
        provider,
        workspace_state: "FAIL",
        state: "FAIL",
        request_id: requestId,
        failure_code: "WORKSPACE_OPEN_REQUEST_FAILED",
        failure_reason: error.message,
      };
      renderWorkspaceStatus(data);
      log(`Claude 工作区启动失败：${error.message}`, "error", "⚠", new Date().toLocaleTimeString());
      return data;
    } finally {
      workspaceOpenRequests.delete(provider);
      setWorkspaceOpenLoading(provider, false);
    }
  })();
  workspaceOpenRequests.set(provider, request);
  return request;
}

async function closeWebAiWorkspace(provider) {
  const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/close`, { method: "POST" });
  const data = await res.json();
  renderWorkspaceStatus(data);
  await loadProviderWorkspaceConsole();
}

async function refreshWorkspaceStatus(provider) {
  if (!els.webAiWorkspaceStatus) return;
  try {
    const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/status`);
    const data = await res.json();
    renderWorkspaceStatus(data);
    await loadProviderWorkspaceConsole();
  } catch (e) {
    els.webAiWorkspaceStatus.innerHTML = `<p class="placeholder">状态加载失败: ${escapeHtml(e.message)}</p>`;
  }
}

async function openAllProviderWorkspaces() {
  for (const provider of ["claude", "chatgpt", "gemini", "kimi", "doubao"]) {
    await openWebAiWorkspace(provider);
  }
}

async function loadProviderWorkspaceConsole() {
  if (!els.providerWorkspaceConsole) return;
  try {
    const data = await fetch(`${API_BASE}/api/web-ai/workspaces/console`).then((res) => res.json());
    const providers = data.providers || {};
    const providerOrder = ["claude", "chatgpt", "gemini", "kimi", "doubao"];
    els.providerWorkspaceConsole.innerHTML = `<div class="provider-console-summary">
      <span>启用工作区：${Number(data.enabled_count || 0)}</span>
      <span>已登录/可用：${Number(data.logged_in_count || 0)}</span>
      <span>可路由：${Number(data.route_ready_count || 0)}</span>
      <span>当前使用：${escapeHtml(providerNames[data.active_provider] || data.active_provider || "无")}</span>
    </div>
    ${providerOrder.map((provider) => renderProviderWorkspaceConsoleCard(provider, providers[provider] || { provider })).join("")}`;
  } catch (error) {
    els.providerWorkspaceConsole.innerHTML = `<p class="placeholder">工作区控制台加载失败：${escapeHtml(error.message)}</p>`;
  }
}

function renderProviderWorkspaceConsoleCard(provider, data) {
  const state = data.workspace_state || data.state || "UNKNOWN";
  const exchange = data.exchange || {};
  const quality = exchange.quality_result || {};
  const needsUser = data.need_user_intervention || ["NEED_LOGIN", "NEED_USER_INTERVENTION", "STALE_CONVERSATION", "PAGE_NETWORK_ERROR"].includes(state);
  return `<article class="provider-console-card workspace-state-${escapeHtml(String(state).toLowerCase())}">
    <header>
      <div><strong>${escapeHtml(providerNames[provider] || provider)}</strong><small>${escapeHtml(workspaceStateLabel(state))}</small></div>
      <span>${data.active_request_id ? "正在回答" : "空闲"}</span>
    </header>
    <div class="provider-console-actions">
      <button class="btn-secondary" data-workspace-open="${provider}" onclick="openWebAiWorkspace('${provider}', this)">打开/聚焦工作区</button>
      <button class="btn-secondary" onclick="refreshWorkspaceStatus('${provider}')">重新检测</button>
      <button class="btn-secondary" onclick="runProviderLiveMinimal('${provider}')">测试连接</button>
      <button class="btn-secondary" onclick="closeWebAiWorkspace('${provider}')">关闭工作区</button>
    </div>
    ${needsUser ? `<p class="warning-text">需要用户处理：${escapeHtml(data.failure_reason || workspaceStateLabel(state))}</p>` : ""}
    <dl>
      <dt>当前 URL</dt><dd>${escapeHtml(data.current_url || data.page_url || "—")}</dd>
      <dt>窗口所有者</dt><dd>${escapeHtml(data.owner_type || "—")} ${data.owner_pid ? `PID ${escapeHtml(String(data.owner_pid))}` : ""}</dd>
      <dt>复用状态</dt><dd>workspace_reused=${data.workspace_reused ? "true" : "false"} · second_context=${data.second_context_created ? "true" : "false"}</dd>
      <dt>最近 prompt</dt><dd>${escapeHtml(exchange.last_prompt || "—")}</dd>
      <dt>最近回答</dt><dd>${escapeHtml(exchange.last_answer_preview || "—")}</dd>
      <dt>质量</dt><dd>${escapeHtml(quality.quality || "—")} ${quality.reason ? `· ${escapeHtml(quality.reason)}` : ""}</dd>
      <dt>warning</dt><dd>${escapeHtml(exchange.warning_class || "—")} ${exchange.warning_text ? `· ${escapeHtml(exchange.warning_text)}` : ""}</dd>
      <dt>evidence</dt><dd>${escapeHtml(exchange.evidence_path || "—")}</dd>
    </dl>
  </article>`;
}

function workspaceStateLabel(state) {
  const labels = {
    READY: "可用",
    PASS: "已测试通过",
    PARTIAL: "可用但不稳定",
    NEED_LOGIN: "需要登录",
    NEED_USER_INTERVENTION: "需要你处理",
    FAIL: "测试失败",
    NOT_CONFIGURED: "未配置",
    STALE_CONVERSATION: "会话已失效",
    PAGE_NETWORK_ERROR: "页面网络错误",
    RETRYABLE_PAGE_ERROR: "页面可重试错误",
    UNKNOWN_ERROR: "未知错误",
    OPEN: "工作区已打开，尚未确认登录",
    OPENING: "正在打开",
    BUSY: "正在回答",
    CRASHED: "工作区已异常关闭",
    CLOSED: "已关闭",
  };
  return labels[state] || state || "UNKNOWN";
}

function workspaceFailureLabel(code, reason = "") {
  const labels = {
    PROJECT_BROWSER_MISSING: "项目专用浏览器未找到",
    PROFILE_IN_USE_BY_BACKEND: "profile 正被占用",
    BROWSER_WINDOW_CREATE_FAILED: "浏览器窗口创建失败",
    PROVIDER_PAGE_OPEN_FAILED: "Claude 页面打开失败",
    WORKSPACE_OPEN_REQUEST_FAILED: "Claude 工作区启动失败",
  };
  return `${labels[code] || "Claude 工作区启动失败"}${reason ? `：${reason}` : ""}`;
}

function renderWorkspaceStatus(data) {
  if (!els.webAiWorkspaceStatus) return;
  if (data.error) {
    els.webAiWorkspaceStatus.innerHTML = `<p class="placeholder">${escapeHtml(data.error)}</p>`;
    return;
  }
  const state = data.workspace_state || data.state || "UNKNOWN";
  const needsUser = data.need_user_intervention || ["NEED_LOGIN", "NEED_USER_INTERVENTION", "STALE_CONVERSATION", "PAGE_NETWORK_ERROR", "RETRYABLE_PAGE_ERROR"].includes(state);
  const actionText = data.suggested_user_action || "请在 Claude 工作区窗口完成登录/验证/页面处理，然后点击“我已处理，继续”。";
  els.webAiWorkspaceStatus.innerHTML = `<div class="memory-item workspace-state-${escapeHtml(state.toLowerCase())}">
    <strong>${escapeHtml(data.provider || "claude")}</strong> · ${escapeHtml(data.state || "UNKNOWN")}<br>
    状态：${escapeHtml(workspaceStateLabel(state))}<br>
    profile: ${escapeHtml(data.profile_dir || "runtime/browser_profiles/claude")}<br>
    url: ${escapeHtml(data.page_url || "—")}<br>
    request: ${escapeHtml(data.request_id || "—")}<br>
    browser: ${data.browser_started ? "started" : "not started"} · page: ${data.page_created ? "created" : "not created"} · visible window: ${data.visible_window_expected ? "expected" : "no"}<br>
    所有者：${escapeHtml(data.owner_type || "—")}${data.owner_pid ? ` · PID ${escapeHtml(String(data.owner_pid))}` : ""}<br>
    当前状态：${escapeHtml(data.active_request_id ? "正在回答" : "空闲")}<br>
    最后使用：${escapeHtml(data.last_activity_at || "—")}<br>
    workspace reused: ${data.workspace_reused ? "yes" : "no"} · second context: ${data.second_context_created ? "yes" : "no"}<br>
    ${needsUser ? `<span class="warning-text">请在 Claude 工作区窗口完成登录/验证/页面处理，然后点击“我已处理，继续”。</span><br><small>${escapeHtml(actionText)}</small><br>` : ""}
    ${data.can_resume ? "<span class=\"success-text\">可继续任务</span><br>" : ""}
    ${data.failure_code ? `<span class="warning-text">${escapeHtml(workspaceFailureLabel(data.failure_code, data.failure_reason))}</span><br><button class="btn-secondary" onclick="openAppData()">查看详细日志</button>` : ""}
    <span>${escapeHtml(data.last_error || "")}</span>
  </div>`;
}

async function testWebAiWorkspace(provider) {
  const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/test`, { method: "POST" });
  const data = await res.json();
  renderWorkspaceStatus(data);
  log(data.message || `${provider} workspace test status refreshed`, "info", "🧪", new Date().toLocaleTimeString());
}

async function resumeWebAiWorkspace(provider) {
  if (pendingExternalAiTaskId) {
    await resumePendingExternalAi();
    return;
  }
  const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/resume`, { method: "POST" });
  const data = await res.json();
  renderWorkspaceStatus(data);
  if (data.can_resume) {
    log(`${provider} 已可继续，原任务可恢复执行`, "success", "▶", new Date().toLocaleTimeString());
  } else {
    log(`${provider} 仍需处理：${data.suggested_user_action || data.state}`, "warning", "⚠", new Date().toLocaleTimeString());
  }
}

async function loadPendingExternalAi() {
  try {
    const res = await fetch(`${API_BASE}/api/external-ai/pending`);
    const data = await res.json();
    const pending = data.pending || [];
    if (pending.length) {
      pendingExternalAiTaskId = pending[0].task_id;
      if (els.externalAiPausePanel) els.externalAiPausePanel.classList.remove("hidden");
      if (els.externalAiPauseReason) {
        const item = pending[0];
        els.externalAiPauseReason.textContent = `${item.provider} 等待处理：${item.failure_reason}. ${item.suggested_user_action}`;
      }
      if (els.currentTaskStatus) els.currentTaskStatus.textContent = pendingExternalAiTaskId;
    }
    return pending;
  } catch (e) {
    log(`加载 pending external AI 失败: ${e.message}`, "warning", "⚠", new Date().toLocaleTimeString());
    return [];
  }
}

async function resumePendingExternalAi() {
  if (!pendingExternalAiTaskId) {
    const pending = await loadPendingExternalAi();
    if (!pending.length) {
      log("没有待恢复的外部 AI 动作", "info", "ℹ", new Date().toLocaleTimeString());
      return;
    }
  }
  const taskId = pendingExternalAiTaskId;
  log(`恢复外部 AI 动作: ${taskId}`, "phase", "▶", new Date().toLocaleTimeString());
  const res = await fetch(`${API_BASE}/api/external-ai/${taskId}/resume`, { method: "POST" });
  const data = await res.json();
  if (data.still_needs_user) {
    if (els.externalAiPausePanel) els.externalAiPausePanel.classList.remove("hidden");
    if (els.externalAiPauseReason) {
      els.externalAiPauseReason.textContent = `${data.provider} 仍需处理：${data.failure_reason}. ${data.suggested_user_action || ""}`;
    }
    renderWorkspaceStatus(data.workspace_status || data);
    log(`仍需处理: ${data.failure_reason}`, "warning", "🙋", new Date().toLocaleTimeString());
    return;
  }
  if (data.success) {
    log("外部 AI 动作恢复成功，继续原任务", "success", "✅", new Date().toLocaleTimeString());
    if (els.externalAiPausePanel) els.externalAiPausePanel.classList.add("hidden");
    if (data.resume_payload?.task_id) {
      await connectContractWebSocket(null, null, data.resume_payload.task_id);
    }
    return;
  }
  log(`外部 AI 恢复失败: ${data.failure_reason || data.error || "unknown"}`, "error", "❌", new Date().toLocaleTimeString());
}

async function showWebAiEvidence(provider) {
  const res = await fetch(`${API_BASE}/api/web-ai/workspace/${provider}/evidence`);
  const data = await res.json();
  const evidence = data.evidence || [];
  if (!evidence.length) {
    renderWorkspaceStatus({ provider, state: "NOT_CONFIGURED", profile_dir: `runtime/browser_profiles/${provider}`, last_error: "暂无 evidence" });
    return;
  }
  els.webAiWorkspaceStatus.innerHTML = evidence.map((item) => `<div class="memory-item">
    <strong>${escapeHtml(provider)} evidence</strong><br>
    path: ${escapeHtml(item.path)}<br>
    screenshot: ${escapeHtml(item.screenshot)}<br>
    metadata: ${escapeHtml(item.metadata)}
  </div>`).join("");
}

async function initWebAiProfile(provider) {
  log(`请手动登录 ${provider}，启动外部浏览器...`, "phase", "🌐", new Date().toLocaleTimeString());
  try {
    await fetch(`${API_BASE}/api/web-ai/profiles/${provider}/init`, { method: "POST" });
    alert(`请在打开的浏览器窗口中手动登录 ${provider}，登录后运行初始化向导。

终端命令: PYTHONPATH=. python scripts/init_web_ai_profile.py --provider ${provider}`);
  } catch (e) {
    log(`初始化失败: ${e.message}`, "error", "❌", new Date().toLocaleTimeString());
  }
  await loadWebAiProfiles();
}

async function testWebAiProfile(provider) {
  log(`测试 ${provider} 连接...`, "phase", "🧪", new Date().toLocaleTimeString());
  try {
    const res = await fetch(`${API_BASE}/api/web-ai/profiles/${provider}/test`, { method: "POST" });
    const data = await res.json();
    if (data.result) {
      log(`${provider}: ${data.result.success ? "PASS" : "FAIL"}`, data.result.success ? "success" : "warning", data.result.success ? "✅" : "❌", new Date().toLocaleTimeString());
    } else if (data.needs_test_run) {
      log(`${provider} 需要在终端运行测试命令`, "warning", "⚠️", new Date().toLocaleTimeString());
    }
  } catch (e) {
    log(`测试失败: ${e.message}`, "error", "❌", new Date().toLocaleTimeString());
  }
  await loadWebAiProfiles();
}

async function resetWebAiProfile(provider) {
  const previewRes = await fetch(`${API_BASE}/api/web-ai/profiles/${provider}/reset`, { method: "POST" });
  const preview = await previewRes.json();
  const profilePath = preview.will_delete?.profile_dir || provider;
  if (!confirm(`确认重置 ${provider} 的项目专用登录 profile？\n\n将删除：${profilePath}\n不会删除其他 provider、settings、evidence 或 tasks。`)) return;
  await fetch(`${API_BASE}/api/web-ai/profiles/${provider}/reset`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ confirm: true }),
  });
  log(`${provider} profile 已重置`, "info", "🗑️", new Date().toLocaleTimeString());
  await loadWebAiProfiles();
  await loadSystemHealth();
}
