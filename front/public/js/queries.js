let currentPage = 1;
let currentQueryId = null;
let pollingTimer = null;
let processingTimer = null;
let procStep = 0;

function initQueries() {
  loadHistory();
  showState('empty');
}

// ─── State ───────────────────────────────────────────────

function showState(state) {
  ['empty', 'create', 'processing', 'result'].forEach((s) => {
    const el = document.getElementById(`state-${s}`);
    if (el) el.classList.toggle('hidden', s !== state);
  });
  if (state !== 'processing') stopProcessingAnimation();
}

// ─── History ─────────────────────────────────────────────

async function loadHistory(page) {
  if (page !== undefined) currentPage = page;

  const container = document.getElementById('query-history');
  const pagination = document.getElementById('pagination');

  try {
    const data = await api.getQueries(currentPage);
    const items = data.items || [];

    if (items.length === 0) {
      container.innerHTML = '<div class="query-list-empty">запросов пока нет</div>';
      pagination.innerHTML = '';
      return;
    }

    container.innerHTML = items.map((q) => queryItemHTML(q)).join('');
    container.querySelectorAll('.query-item').forEach((el) => {
      el.addEventListener('click', () => selectQuery(el.dataset.id));
    });

    const totalPages = Math.ceil(data.total / data.size);
    if (totalPages > 1) {
      let html = '';
      for (let i = 1; i <= totalPages; i++) {
        html += `<button class="${i === currentPage ? 'active' : ''}" onclick="loadHistory(${i})">${i}</button>`;
      }
      pagination.innerHTML = html;
    } else {
      pagination.innerHTML = '';
    }
  } catch {
    container.innerHTML = '<div class="query-list-empty">ошибка загрузки</div>';
  }
}

function queryItemHTML(q) {
  const status = getQueryStatus(q);
  const date = new Date(q.created_at).toLocaleDateString('ru-RU', {
    day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
  });
  const active = q.id === currentQueryId ? ' active' : '';
  const text = escapeHTML(q.text || '').substring(0, 100);

  return `
    <div class="query-item${active}" data-id="${q.id}">
      <div class="query-item-text">${text}</div>
      <div class="query-item-meta">
        <span class="query-status ${status}"></span>
        <span>${date}</span>
      </div>
    </div>`;
}

function getQueryStatus(q) {
  if (q.response_text || q.responded_at) return 'completed';
  return 'processing';
}

// ─── Select query ─────────────────────────────────────────

async function selectQuery(id) {
  currentQueryId = id;
  stopPolling();

  document.querySelectorAll('.query-item').forEach((el) => {
    el.classList.toggle('active', el.dataset.id === id);
  });

  try {
    const query = await api.getQuery(id);
    if (query.response_text) {
      showResult(query, false);
    } else {
      showProcessing(query);
      startPolling(id);
    }
  } catch {
    showState('empty');
  }
}

// ─── Processing state ─────────────────────────────────────

function showProcessing(query) {
  document.getElementById('processing-text').textContent = query.text;
  showState('processing');
  startProcessingAnimation();
}

function startProcessingAnimation() {
  stopProcessingAnimation();
  procStep = 0;
  updateProcSteps();
  processingTimer = setInterval(() => {
    procStep = (procStep + 1) % 4;
    updateProcSteps();
  }, 2200);
}

function stopProcessingAnimation() {
  if (processingTimer) {
    clearInterval(processingTimer);
    processingTimer = null;
  }
  for (let i = 0; i < 4; i++) {
    const el = document.getElementById(`proc-step-${i}`);
    if (el) el.classList.remove('step-active', 'step-done');
  }
}

function updateProcSteps() {
  for (let i = 0; i < 4; i++) {
    const el = document.getElementById(`proc-step-${i}`);
    if (!el) continue;
    el.classList.remove('step-active', 'step-done');
    if (i < procStep)      el.classList.add('step-done');
    else if (i === procStep) el.classList.add('step-active');
  }
}

// ─── Result state ─────────────────────────────────────────

async function showResult(query, animate = false) {
  document.getElementById('result-query-text').textContent = query.text;

  const createdAt = new Date(query.created_at).toLocaleString('ru-RU');
  document.getElementById('result-created').textContent = `создан: ${createdAt}`;

  if (query.responded_at) {
    const respondedAt = new Date(query.responded_at).toLocaleString('ru-RU');
    document.getElementById('result-responded').textContent = `ответ: ${respondedAt}`;
  } else {
    document.getElementById('result-responded').textContent = '';
  }

  showState('result');

  const responseEl = document.getElementById('result-response-text');
  const responseText = query.response_text || 'ответ пока не получен';

  if (animate) {
    await typewriter(responseEl, responseText);
  } else {
    responseEl.textContent = responseText;
  }

  // Similar tasks
  try {
    const tasks = await api.getSimilarTasks(query.id);
    const section = document.getElementById('similar-tasks-section');
    const list = document.getElementById('similar-tasks-list');

    if (tasks && tasks.length > 0) {
      list.innerHTML = tasks.map((t) => `
        <div class="similar-task-item">
          <span class="task-title">${escapeHTML(t.title)}</span>
          <span class="task-links">
            ${t.task_url ? `<a href="${escapeHTML(t.task_url)}" target="_blank" rel="noopener">задача ↗</a>` : ''}
            ${t.solution_url ? `<a href="${escapeHTML(t.solution_url)}" target="_blank" rel="noopener">решение ↗</a>` : ''}
          </span>
        </div>`).join('');
      section.classList.remove('hidden');
    } else {
      section.classList.add('hidden');
    }
  } catch {
    document.getElementById('similar-tasks-section').classList.add('hidden');
  }
}

// ─── Typewriter ───────────────────────────────────────────

function typewriter(el, text, speed = 7) {
  return new Promise((resolve) => {
    el.textContent = '';
    let i = 0;
    function tick() {
      if (i < text.length) {
        el.textContent += text[i++];
        setTimeout(tick, speed);
      } else {
        resolve();
      }
    }
    tick();
  });
}

// ─── Polling ──────────────────────────────────────────────

function startPolling(id) {
  pollingTimer = setInterval(async () => {
    try {
      const query = await api.getQuery(id);
      if (query.response_text) {
        stopPolling();
        showResult(query, true);
        loadHistory();
      }
    } catch {
      stopPolling();
    }
  }, 3000);
}

function stopPolling() {
  if (pollingTimer) {
    clearInterval(pollingTimer);
    pollingTimer = null;
  }
}

// ─── New query ────────────────────────────────────────────

document.getElementById('new-query-btn').addEventListener('click', () => {
  currentQueryId = null;
  stopPolling();
  document.querySelectorAll('.query-item').forEach((el) => el.classList.remove('active'));
  const ta = document.getElementById('query-text');
  ta.value = '';
  autoResizeTextarea(ta);
  document.getElementById('query-create-error').textContent = '';
  showState('create');
  ta.focus();
});

// ─── Auto-expanding textarea ─────────────────────────────

function autoResizeTextarea(el) {
  el.style.height = 'auto';
  el.style.height = el.scrollHeight + 'px';
}

const queryTextarea = document.getElementById('query-text');

queryTextarea.addEventListener('input', () => {
  autoResizeTextarea(queryTextarea);
});

// Enter to submit (Shift+Enter for newline)
queryTextarea.addEventListener('keydown', (e) => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    document.getElementById('query-form').requestSubmit();
  }
});

// ─── Submit query ────────────────────────────────────────

document.getElementById('query-form').addEventListener('submit', async (e) => {
  e.preventDefault();
  const errorEl = document.getElementById('query-create-error');
  errorEl.textContent = '';

  const text = document.getElementById('query-text').value.trim();
  if (!text) return;

  const submitBtn = e.target.querySelector('.chat-send-btn');
  submitBtn.disabled = true;

  try {
    const result = await api.createQuery(text);
    const queryId = String(result.query_id);
    currentQueryId = queryId;
    await loadHistory();
    showProcessing({ text });
    startPolling(queryId);
  } catch (err) {
    errorEl.textContent = err.message;
  } finally {
    submitBtn.disabled = false;
  }
});

// ─── Utils ────────────────────────────────────────────────

function escapeHTML(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

if (api.isAuthenticated()) {
  initQueries();
}
