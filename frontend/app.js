/* ============================================================
   Local AI Orchestrator — Frontend Logic
   ============================================================ */

const API_BASE = window.location.origin.includes("localhost")
  ? "http://localhost:8422"
  : window.location.origin;
const WS_BASE = API_BASE.replace(/^http/, "ws");

let ws = null;
let stepCount = 0;
let successCount = 0;
let failCount = 0;
let evidenceCount = 0;
let logCounter = 0;

const els = {
  llmStatus: document.getElementById("llmStatus"),
  llmStatusText: document.getElementById("llmStatusText"),
  goalDisplay: document.getElementById("goalDisplay"),
  criteriaList: document.getElementById("criteriaList"),
  aiProfiles: document.getElementById("aiProfiles"),
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
};

async function init() {
  await loadSkills();
  await loadAiProfiles();
  await loadPendingConfirmations();
  await loadResumableTasks();
  await loadWebAiProfiles();
  initCapabilities();
  togglePreflight();
  connectWebSocket();
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
    case "step_start":
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
      log(
        `任务结束. 成功率: ${(data.success_rate * 100).toFixed(0)}%`,
        data.verified ? "success" : "warning",
        "🏁",
        time,
      );
      break;
    case "stopped":
      finishUi();
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
  els.executeBtn.innerHTML = '<span class="btn-icon">▶</span> 执行任务';
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

async function resumeTask(taskId) {
  log(`恢复任务 ${taskId}`, "phase", "🔁", new Date().toLocaleTimeString());
  resetUi();
  try {
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
    const providers = ["chatgpt", "claude", "doubao", "gemini", "kimi"];
    let html = '<div style="display:flex;flex-direction:column;gap:6px;">';
    for (const provider of providers) {
      const p = profiles[provider] || {
        test_status: "not_run",
        logged_in: false,
        initialized: false,
      };
      const dotClass =
        p.test_status === "PASS"
          ? "available"
          : p.test_status === "PARTIAL"
          ? "available"
          : "unavailable";
      const testedLabel = p.test_summary?.created_at
        ? new Date(p.test_summary.created_at).toLocaleDateString()
        : "—";
      html += `<div class="ai-profile-item" style="flex-direction:column;align-items:flex-start;gap:2px;">
        <div class="ai-profile-dot ${dotClass}"></div>
        <span><strong>${escapeHtml(provider)}</strong></span>
        <small>${escapeHtml(p.test_status)} · logged_in:${p.logged_in} · tested:${testedLabel}</small>
        <div style="display:flex;gap:4px;margin-top:2px;">
          <button class="btn-secondary" onclick="initWebAiProfile('${provider}')" style="font-size:10px;padding:2px 6px;">Init</button>
          <button class="btn-secondary" onclick="testWebAiProfile('${provider}')" style="font-size:10px;padding:2px 6px;">Test</button>
          <button class="btn-secondary" onclick="resetWebAiProfile('${provider}')" style="font-size:10px;padding:2px 6px;">Reset</button>
        </div>
      </div>`;
    }
    html += "</div>";
    container.innerHTML = html;
  } catch (e) {
    /* non-critical */
  }
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
  if (!confirm(`确认重置 ${provider} 的 profile 和测试数据？`)) return;
  await fetch(`${API_BASE}/api/web-ai/profiles/${provider}/reset`, { method: "POST" });
  log(`${provider} profile 已重置`, "info", "🗑️", new Date().toLocaleTimeString());
  await loadWebAiProfiles();
}
