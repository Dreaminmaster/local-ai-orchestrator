/* ============================================================
   Local AI Orchestrator — Frontend Logic
   ============================================================ */

const API_BASE = window.location.origin.includes('localhost') 
    ? 'http://localhost:8422' 
    : window.location.origin;
const WS_BASE = API_BASE.replace(/^http/, 'ws');

let ws = null;
let stepCount = 0;
let successCount = 0;
let failCount = 0;
let evidenceCount = 0;
let logCounter = 0;

const els = {
    llmStatus: document.getElementById('llmStatus'),
    llmStatusText: document.getElementById('llmStatusText'),
    goalDisplay: document.getElementById('goalDisplay'),
    criteriaList: document.getElementById('criteriaList'),
    aiProfiles: document.getElementById('aiProfiles'),
    skillsList: document.getElementById('skillsList'),
    taskInput: document.getElementById('taskInput'),
    executeBtn: document.getElementById('executeBtn'),
    planSteps: document.getElementById('planSteps'),
    logContainer: document.getElementById('logContainer'),
    logCount: document.getElementById('logCount'),
    reportArea: document.getElementById('reportArea'),
    reportContent: document.getElementById('reportContent'),
    evidenceBoard: document.getElementById('evidenceBoard'),
    statSteps: document.getElementById('statSteps'),
    statSuccess: document.getElementById('statSuccess'),
    statFailed: document.getElementById('statFailed'),
    statEvidence: document.getElementById('statEvidence'),
    taskMemory: document.getElementById('taskMemory')
};

async function init() {
    await loadSkills();
    await loadAiProfiles();
    connectWebSocket();
}

async function loadSkills() {
    try {
        const res = await fetch(`${API_BASE}/api/skills`);
        const data = await res.json();
        els.skillsList.innerHTML = '';
        data.skills.forEach(skill => {
            const el = document.createElement('div');
            el.className = 'skill-tag';
            el.textContent = skill.name;
            el.title = `${skill.description}\nRisk: ${skill.risk_level}`;
            els.skillsList.appendChild(el);
        });
    } catch (e) {
        console.error('Failed to load skills:', e);
    }
}

async function loadAiProfiles() {
    try {
        const res = await fetch(`${API_BASE}/api/ai-profiles`);
        const data = await res.json();
        els.aiProfiles.innerHTML = '';
        data.profiles.forEach(p => {
            const el = document.createElement('div');
            el.className = 'ai-profile-item';
            el.innerHTML = `
                <div class="ai-profile-dot ${p.status === 'available' ? 'available' : 'unavailable'}"></div>
                <span>${p.name}</span>
            `;
            els.aiProfiles.appendChild(el);
        });
    } catch (e) {
        console.error('Failed to load AI profiles:', e);
    }
}

function connectWebSocket() {
    els.llmStatus.className = 'status-dot connecting';
    els.llmStatusText.textContent = '连接中...';
    ws = new WebSocket(`${WS_BASE}/ws/execute`);
    ws.onopen = () => {
        els.llmStatus.className = 'status-dot connected';
        els.llmStatusText.textContent = '已连接';
    };
    ws.onmessage = event => handleEvent(JSON.parse(event.data));
    ws.onclose = () => {
        els.llmStatus.className = 'status-dot';
        els.llmStatusText.textContent = '未连接';
        setTimeout(connectWebSocket, 3000);
    };
    ws.onerror = e => console.error('WebSocket error:', e);
}

function executeTask() {
    const input = els.taskInput.value.trim();
    if (!input) return;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
        alert('WebSocket 未连接，请稍后重试。');
        return;
    }
    resetUi();
    ws.send(JSON.stringify({ user_input: input }));
}

function resetUi() {
    els.executeBtn.disabled = true;
    els.executeBtn.innerHTML = '<span class="btn-icon">⏳</span> 执行中...';
    els.goalDisplay.innerHTML = '<p class="placeholder">分析中...</p>';
    els.criteriaList.innerHTML = '';
    els.planSteps.innerHTML = '';
    els.logContainer.innerHTML = '';
    els.evidenceBoard.innerHTML = '';
    els.reportArea.style.display = 'none';
    els.taskMemory.innerHTML = '';
    stepCount = 0; successCount = 0; failCount = 0; evidenceCount = 0; logCounter = 0;
    updateStats();
}

function handleEvent(event) {
    const { type, data, timestamp } = event;
    const time = new Date(timestamp).toLocaleTimeString();
    switch (type) {
        case 'phase': log(data.message, 'phase', '🔄', time); break;
        case 'goal': renderGoal(data.goal); log('任务目标已解析', 'success', '🎯', time); break;
        case 'plan': renderPlan(data.plan); log(`生成执行计划，共 ${data.plan.total_steps} 步`, 'info', '📋', time); break;
        case 'step_start': updateStepStatus(data.step, 'active'); log(`[Step ${data.step}/${data.total}] ${data.goal}`, 'info', '▶️', time); break;
        case 'gap_detected': log(`发现能力缺口: ${data.gap.gap_type}`, 'warning', '⚠️', time); addMemory(`缺口: ${data.gap.gap_type}`); break;
        case 'skills_selected': log(`调用技能链: ${data.chain.join(' → ')}`, 'info', '🔧', time); break;
        case 'step_result': handleStepResult(data, time); break;
        case 'failure_repair': log(`失败诊断: ${data.repair.symptom || 'unknown'}`, 'warning', '🔧', time); break;
        case 'verification': log(data.result.verified ? '最终校验通过' : '最终校验未通过', data.result.verified ? 'success' : 'error', data.result.verified ? '✅' : '❌', time); break;
        case 'report': els.reportArea.style.display = 'block'; els.reportContent.textContent = data.report; log('生成最终报告', 'info', '📝', time); break;
        case 'complete': finishUi(); log(`任务结束. 成功率: ${(data.success_rate * 100).toFixed(0)}%`, data.verified ? 'success' : 'warning', '🏁', time); break;
        case 'stopped': finishUi(); log(`任务停止: ${data.reason}`, 'warning', '🛑', time); break;
        case 'need_user': finishUi(); log(`需要用户确认: ${data.reason}`, 'warning', '🙋', time); break;
        case 'error': finishUi(); log(`系统错误: ${data.message}`, 'error', '💥', time); break;
    }
}

function handleStepResult(data, time) {
    updateStepStatus(data.step, data.success ? 'completed' : 'failed');
    if (data.success) { successCount++; log(`步骤 ${data.step} 执行成功`, 'success', '✅', time); }
    else { failCount++; log(`步骤 ${data.step} 执行失败`, 'error', '❌', time); }
    stepCount++; updateStats();
    data.results.forEach(r => {
        if (r.evidence && r.evidence.length) r.evidence.forEach(ev => addEvidence(r.skill, ev, r.success));
        else if (r.result) addEvidence(r.skill, r.result.substring(0, 80) + '...', r.success);
        else if (r.error) addEvidence(r.skill, r.error.substring(0, 80) + '...', false);
    });
}

function finishUi() {
    els.executeBtn.disabled = false;
    els.executeBtn.innerHTML = '<span class="btn-icon">▶</span> 执行任务';
}

function renderGoal(goal) {
    els.goalDisplay.innerHTML = `
        <div><strong>目标:</strong> ${escapeHtml(goal.main_goal || '')}</div>
        <div style="margin-top:4px; font-size:12px; color:var(--text-secondary)">
            <strong>类型:</strong> ${escapeHtml(goal.task_type || 'general')} | <strong>复杂度:</strong> ${escapeHtml(goal.estimated_complexity || 'medium')}
        </div>`;
    els.criteriaList.innerHTML = '';
    (goal.success_criteria || []).forEach(c => {
        const li = document.createElement('li'); li.textContent = c; els.criteriaList.appendChild(li);
    });
}

function renderPlan(planData) {
    els.planSteps.innerHTML = '';
    (planData.plan || []).forEach(step => {
        const stepEl = document.createElement('div');
        stepEl.className = 'plan-step'; stepEl.id = `step-${step.step}`;
        const skillsHtml = (step.needed_skills || []).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');
        stepEl.innerHTML = `<div class="step-number">${step.step}</div><div class="step-content"><div>${escapeHtml(step.goal || '')}</div></div><div class="step-skills">${skillsHtml}</div>`;
        els.planSteps.appendChild(stepEl);
    });
}

function updateStepStatus(stepNum, status) {
    const el = document.getElementById(`step-${stepNum}`);
    if (el) el.className = `plan-step ${status}`;
}

function log(msg, type = 'info', icon = '•', time = '') {
    const el = document.createElement('div');
    el.className = `log-entry ${type}`;
    el.innerHTML = `<span class="log-time">[${time}]</span><span class="log-icon">${icon}</span><span class="log-text">${escapeHtml(msg)}</span>`;
    els.logContainer.appendChild(el);
    els.logContainer.scrollTop = els.logContainer.scrollHeight;
    logCounter++; els.logCount.textContent = logCounter;
}

function addEvidence(source, content, isSuccess) {
    const el = document.createElement('div');
    el.className = `evidence-item ${!isSuccess ? 'error-evidence' : ''}`;
    el.innerHTML = `<div class="evidence-type">${escapeHtml(source)}</div><div class="evidence-content">${escapeHtml(String(content))}</div>`;
    if (els.evidenceBoard.querySelector('.placeholder')) els.evidenceBoard.innerHTML = '';
    els.evidenceBoard.appendChild(el);
    evidenceCount++; updateStats();
}

function addMemory(text) {
    const el = document.createElement('div'); el.className = 'memory-item'; el.textContent = text;
    if (els.taskMemory.querySelector('.placeholder')) els.taskMemory.innerHTML = '';
    els.taskMemory.appendChild(el);
}

function updateStats() {
    els.statSteps.textContent = stepCount;
    els.statSuccess.textContent = successCount;
    els.statFailed.textContent = failCount;
    els.statEvidence.textContent = evidenceCount;
}

function escapeHtml(str) {
    return String(str).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
}

init();
