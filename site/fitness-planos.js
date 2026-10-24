(() => {
  const $ = (selector) => document.querySelector(selector);
  const days = ['Domingo', 'Segunda-feira', 'Terça-feira', 'Quarta-feira', 'Quinta-feira', 'Sexta-feira', 'Sábado'];
  const names = { A: 'Pernas', B: 'Costas', C: 'Core', D: 'Geral' };
  const colors = { A: '#20c8d8', B: '#a27bff', C: '#ffb563', D: '#35d79b' };
  let catalog = [], groups = [];
  let people = [], personId = '', state = null, selectedCode = 'A', saving = false;

  function uid() {
    return window.crypto?.randomUUID ? window.crypto.randomUUID() : 'plan-' + Date.now().toString(36) + Math.random().toString(36).slice(2);
  }
  function clone(value) { return JSON.parse(JSON.stringify(value)); }
  function setStatus(message, kind = 'loading') {
    const el = $('#planSqlStatus');
    el.textContent = message;
    el.dataset.state = kind;
  }
  async function apiGet(url) {
    const response = await fetch(url, { cache: 'no-store' });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `Servidor respondeu ${response.status}`);
    return data;
  }
  function defaultExercise(code, id, sets, reps) {
    const item = catalog.find((exercise) => exercise.id === id);
    return { id: uid(), catalogId: item.id, muscleGroup: item.muscleGroup, name: item.name, mode: item.mode, sets, reps, durationMinutes: null };
  }
  function starterState(revision = 0) {
    const data = {
      revision,
      plans: [
        { code: 'A', name: names.A, exercises: [defaultExercise('A', 'leg-press', 3, 10), defaultExercise('A', 'leg-extension', 2, 12), defaultExercise('A', 'seated-leg-curl', 3, 12), defaultExercise('A', 'hip-thrust', 3, 10)] },
        { code: 'B', name: names.B, exercises: [defaultExercise('B', 'lat-pulldown', 3, 10), defaultExercise('B', 'seated-row', 3, 10), defaultExercise('B', 'chest-supported-row', 2, 12), defaultExercise('B', 'face-pull', 2, 12)] },
        { code: 'C', name: names.C, exercises: [defaultExercise('C', 'dead-bug', 3, 10), defaultExercise('C', 'pallof-press', 3, 10), defaultExercise('C', 'bird-dog', 2, 8), defaultExercise('C', 'abdominal-crunch', 2, 12)] },
        { code: 'D', name: names.D, exercises: [defaultExercise('D', 'box-squat', 2, 10), defaultExercise('D', 'chest-press', 3, 10), defaultExercise('D', 'lat-pulldown', 3, 10), defaultExercise('D', 'hip-thrust', 2, 12), defaultExercise('D', 'dead-bug', 2, 10)] }
      ],
      schedule: [{ weekday: 1, planCode: 'A', time: null }, { weekday: 3, planCode: 'B', time: null }]
    };
    for (const plan of data.plans) plan.id = uid();
    return data;
  }
  function renderPeople() {
    const select = $('#planPerson');
    select.innerHTML = people.map((person) => `<option value="${escapeHtml(person.id)}">${escapeHtml(person.name)}</option>`).join('');
    select.value = personId;
  }
  function escapeHtml(value) { return String(value ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c])); }
  function renderCards() {
    const container = $('#planCards'); container.replaceChildren();
    (state?.plans || []).slice().sort((a, b) => a.code.localeCompare(b.code)).forEach((plan) => {
      const button = document.createElement('button'); button.type = 'button'; button.className = 'plan-card' + (plan.code === selectedCode ? ' active' : ''); button.style.setProperty('--accent', colors[plan.code]);
      const code = document.createElement('span'); code.className = 'plan-card-code'; code.textContent = `TREINO ${plan.code}`;
      const name = document.createElement('span'); name.className = 'plan-card-name'; name.textContent = plan.name;
      const meta = document.createElement('span'); meta.className = 'plan-card-meta'; meta.textContent = `${plan.exercises.length} exercício${plan.exercises.length === 1 ? '' : 's'}`;
      button.append(code, name, meta); button.addEventListener('click', () => { selectedCode = plan.code; render(); $('#planEditor').scrollIntoView({ behavior: 'smooth', block: 'nearest' }); }); container.append(button);
    });
  }
  function renderSchedule() {
    const container = $('#scheduleRows'); container.replaceChildren();
    $('#scheduleEmpty').hidden = state.schedule.length > 0;
    $('#schedulePersonName').textContent = `${people.find((person) => person.id === personId)?.name || ''} · repete toda semana`;
    state.schedule.slice().sort((a, b) => a.weekday - b.weekday).forEach((slot, index) => {
      const row = document.createElement('div'); row.className = 'schedule-row';
      const day = document.createElement('select'); day.className = 'schedule-day'; day.setAttribute('aria-label', 'Dia da semana');
      days.forEach((label, value) => { const option = document.createElement('option'); option.value = value; option.textContent = label; day.append(option); }); day.value = slot.weekday;
      const plan = document.createElement('select'); plan.setAttribute('aria-label', 'Ficha de treino');
      state.plans.forEach((item) => { const option = document.createElement('option'); option.value = item.code; option.textContent = `Treino ${item.code} · ${item.name}`; plan.append(option); }); plan.value = slot.planCode;
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'remove-schedule'; remove.textContent = '×'; remove.setAttribute('aria-label', 'Remover dia');
      const sourceWeekday = slot.weekday;
      const change = async (field, value) => { const previous = clone(state), target = state.schedule.find((item) => item.weekday === sourceWeekday); if (!target) return; target[field] = field === 'weekday' ? Number(value) : (value || null); if (!await saveState(previous)) return; renderSchedule(); renderCards(); };
      day.addEventListener('change', () => change('weekday', day.value)); plan.addEventListener('change', () => change('planCode', plan.value));
      remove.addEventListener('click', async () => { const previous = clone(state), sourceIndex = state.schedule.findIndex((item) => item.weekday === sourceWeekday); if (sourceIndex < 0) return; state.schedule.splice(sourceIndex, 1); if (await saveState(previous)) render(); });
      row.append(day, plan, remove); container.append(row);
    });
  }
  function renderEditor() {
    const plan = state?.plans.find((item) => item.code === selectedCode);
    $('#planEditor').hidden = !plan;
    if (!plan) return;
    $('#editorEyebrow').textContent = `FICHA ${plan.code}`;
    $('#editorEyebrow').style.color = colors[plan.code];
    $('#planNameInput').value = plan.name;
    const list = $('#planExerciseList'); list.replaceChildren();
    $('#planExerciseEmpty').hidden = plan.exercises.length > 0;
    plan.exercises.forEach((exercise, index) => {
      const row = document.createElement('div'); row.className = 'plan-exercise-row';
      const order = document.createElement('span'); order.className = 'plan-order'; order.textContent = String(index + 1).padStart(2, '0');
      const name = document.createElement('span'); name.className = 'plan-exercise-name'; name.textContent = exercise.name;
      const group = document.createElement('small'); group.textContent = exercise.muscleGroup; name.append(group);
      const video = exercise.youtubeUrl ? document.createElement('a') : document.createElement('button');
      video.className = 'exercise-video' + (exercise.youtubeUrl ? '' : ' unavailable');
      if (exercise.youtubeUrl) { video.href = exercise.youtubeUrl; video.target = '_blank'; video.rel = 'noopener noreferrer'; } else { video.type = 'button'; video.disabled = true; }
      video.textContent = '▶'; video.title = exercise.youtubeUrl ? `Assistir vídeo: ${exercise.name}` : 'Cadastre um link do YouTube para este exercício'; video.setAttribute('aria-label', video.title); name.prepend(video);
      const fields = document.createElement('span'); fields.className = 'plan-row-fields';
      const makeNumberInput = (value, label, property, min, max) => {
        const input = document.createElement('input'); input.type = 'number'; input.min = String(min); input.max = String(max); input.value = value ?? ''; input.setAttribute('aria-label', label); input.title = label;
        input.addEventListener('change', () => updateExercise(index, property, Number(input.value)));
        return input;
      };
      if (exercise.mode === 'cardio') {
        fields.append(makeNumberInput(exercise.durationMinutes, 'Tempo de cardio em minutos', 'durationMinutes', 1, 1440));
        const suffix = document.createElement('small'); suffix.textContent = 'min cardio'; fields.append(suffix);
      } else {
        fields.append(makeNumberInput(exercise.sets, 'Séries planejadas', 'sets', 1, 20));
        const separator = document.createElement('small'); separator.textContent = 'séries ×'; fields.append(separator);
        fields.append(makeNumberInput(exercise.reps, 'Repetições planejadas', 'reps', 1, 100));
        const suffix = document.createElement('small'); suffix.textContent = 'reps'; fields.append(suffix);
      }
      const actions = document.createElement('span'); actions.className = 'plan-row-actions';
      const up = document.createElement('button'); up.type = 'button'; up.textContent = '↑'; up.setAttribute('aria-label', 'Mover exercício para cima'); up.disabled = index === 0;
      const down = document.createElement('button'); down.type = 'button'; down.textContent = '↓'; down.setAttribute('aria-label', 'Mover exercício para baixo'); down.disabled = index === plan.exercises.length - 1;
      const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'remove'; remove.textContent = '×'; remove.setAttribute('aria-label', 'Remover exercício');
      up.addEventListener('click', () => moveExercise(index, -1)); down.addEventListener('click', () => moveExercise(index, 1)); remove.addEventListener('click', () => removeExercise(index));
      actions.append(up, down, remove); row.append(order, name, fields, actions); list.append(row);
    });
  }
  function render() { renderPeople(); renderCards(); renderSchedule(); renderEditor(); }
  async function saveState(previous, successMessage = 'Alterações gravadas no banco SQLite do servidor.') {
    if (saving) {
      if (previous) { state = previous; render(); }
      setStatus('Aguarde a gravação atual no SQL terminar antes de fazer outra alteração.', 'saving');
      return false;
    }
    saving = true; setStatus('Gravando alterações no SQL do servidor…', 'saving');
    try {
      const response = await fetch('/fitness-api', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ action: 'save_plans', personId, expectedRevision: state.revision, plans: state.plans, schedule: state.schedule }) });
      const result = await response.json();
      if (!response.ok || !result.ok) {
        if (response.status === 409 && result.conflict) await loadPersonPlans(false);
        else if (previous) { state = previous; render(); }
        throw new Error(result.error || 'Não foi possível gravar no SQL.');
      }
      state.revision = result.revision;
      setStatus(successMessage, 'saved');
      return true;
    } catch (error) {
      console.error(error);
      setStatus(`${error.message} Nenhuma alteração ficou salva apenas no navegador.`, 'error');
      return false;
    } finally { saving = false; }
  }
  async function loadPersonPlans(seedIfEmpty = true) {
    setStatus('Lendo fichas e agenda do banco SQL…', 'loading');
    try {
      const data = await apiGet(`/fitness-api?action=plans&person=${encodeURIComponent(personId)}`);
      if (!data.personExists) throw new Error('Este perfil ainda não está gravado no SQL. Abra a página Fitness conectado e tente novamente.');
      state = { revision: data.revision, plans: data.plans, schedule: data.schedule };
      if (state.plans.length === 0 && seedIfEmpty) {
        const empty = clone(state); state = starterState(data.revision); render();
        if (!await saveState(empty, 'Fichas iniciais gravadas no banco SQL do servidor.')) { state = null; render(); return; }
      }
      if (state.plans.length !== 4) throw new Error('O SQL precisa ter as quatro fichas A, B, C e D. Recarregue para sincronizar.');
      render();
      if (data.plans.length > 0) setStatus('Fichas e agenda carregadas do banco SQL do servidor.', 'saved');
    } catch (error) {
      state = null; render(); setStatus(`${error.message} O editor não grava planos offline.`, 'error');
    }
  }
  async function choosePerson(id) {
    if (saving) return;
    if (id === personId && state) return;
    personId = id; state = null; renderPeople(); $('#planPerson').value = id;
    const url = new URL(location.href); url.searchParams.set('person', id); history.replaceState(null, '', url);
    await loadPersonPlans();
  }
  function fillExerciseCatalog() {
    const group = $('#muscleFilter').value;
    const matches = catalog.filter((exercise) => exercise.muscleGroup === group);
    const select = $('#exerciseChoice'); select.replaceChildren();
    matches.forEach((exercise) => { const option = document.createElement('option'); option.value = exercise.id; option.textContent = exercise.name; select.append(option); });
    const cardio = matches[0]?.mode === 'cardio';
    document.querySelectorAll('.strength-field').forEach((el) => { el.hidden = cardio; });
    document.querySelectorAll('.cardio-field').forEach((el) => { el.hidden = !cardio; });
  }
  async function addExercise() {
    if (!state) return;
    const item = catalog.find((exercise) => exercise.id === $('#exerciseChoice').value);
    if (!item) return;
    const exercise = item.mode === 'cardio'
      ? { id: uid(), catalogId: item.id, muscleGroup: item.muscleGroup, name: item.name, mode: 'cardio', sets: null, reps: null, durationMinutes: Number($('#exerciseDuration').value) }
      : { id: uid(), catalogId: item.id, muscleGroup: item.muscleGroup, name: item.name, mode: 'strength', sets: Number($('#exerciseSets').value), reps: Number($('#exerciseReps').value), durationMinutes: null };
    if ((item.mode === 'cardio' && (!exercise.durationMinutes || exercise.durationMinutes < 1)) || (item.mode === 'strength' && (!exercise.sets || exercise.sets < 1 || !exercise.reps || exercise.reps < 1))) { setStatus('Preencha séries/repetições ou o tempo de cardio em minutos.', 'error'); return; }
    const previous = clone(state); state.plans.find((plan) => plan.code === selectedCode).exercises.push(exercise); render();
    if (await saveState(previous, `${item.name} gravado no SQL na ficha ${selectedCode}.`)) render();
  }
  async function removeExercise(index) {
    const previous = clone(state); state.plans.find((plan) => plan.code === selectedCode).exercises.splice(index, 1); render();
    if (await saveState(previous, 'Exercício removido do SQL.')) render();
  }
  async function updateExercise(index, property, value) {
    if (!state || !Number.isFinite(value) || value < 1) { renderEditor(); setStatus('Use um número válido maior que zero.', 'error'); return; }
    const previous = clone(state), exercise = state.plans.find((plan) => plan.code === selectedCode).exercises[index];
    exercise[property] = value;
    if (await saveState(previous, 'Séries, repetições ou tempo atualizados no SQL.')) renderEditor();
  }
  async function moveExercise(index, offset) {
    const previous = clone(state), list = state.plans.find((plan) => plan.code === selectedCode).exercises;
    [list[index], list[index + offset]] = [list[index + offset], list[index]]; render();
    if (await saveState(previous, 'Ordem dos exercícios gravada no SQL.')) render();
  }
  async function addScheduleDay() {
    if (!state) return;
    const used = new Set(state.schedule.map((slot) => slot.weekday));
    const weekday = days.findIndex((_, index) => !used.has(index));
    if (weekday < 0) { setStatus('Todos os dias já têm um treino planejado.', 'error'); return; }
    const previous = clone(state); state.schedule.push({ weekday, planCode: selectedCode, time: null });
    if (await saveState(previous, `${days[weekday]} gravada na agenda do SQL.`)) render();
  }
  $('#muscleFilter').addEventListener('change', fillExerciseCatalog);
  $('#addPlanExercise').addEventListener('click', addExercise);
  $('#addScheduleDay').addEventListener('click', addScheduleDay);
  $('#planPerson').addEventListener('change', (event) => choosePerson(event.target.value));
  $('#planNameInput').addEventListener('change', async (event) => {
    if (!state) return;
    const plan = state.plans.find((item) => item.code === selectedCode), value = event.target.value.trim();
    if (!value || value === plan.name) { event.target.value = plan.name; return; }
    const previous = clone(state); plan.name = value;
    if (await saveState(previous, `Nome da ficha ${selectedCode} gravado no SQL.`)) render();
  });

  async function init() {
    $('#addScheduleDay').disabled = true;
    try {
      const data = await apiGet('/fitness-api');
      if (!data.initialized) throw new Error('Ainda não há perfis no SQL. Abra o Fitness conectado para sincronizar os perfis primeiro.');
      people = (data.people || []).filter((person) => !person.deletedAt);
      if (!people.length) throw new Error('Cadastre uma pessoa na página Fitness antes de montar os planos.');
      const catalogData = await apiGet('/fitness-api?action=catalog');
      catalog = catalogData.catalog || [];
      groups = [...new Set(catalog.map((item) => item.muscleGroup))];
      if (!groups.length) throw new Error('O catálogo SQL não tem exercícios disponíveis.');
      $('#muscleFilter').innerHTML = groups.map((group) => `<option>${escapeHtml(group)}</option>`).join('');
      fillExerciseCatalog();
      const requested = new URLSearchParams(location.search).get('person');
      let remembered = '';
      try { remembered = localStorage.getItem('mov_active_person') || ''; } catch (_) { /* Apenas preferência de perfil, não contém dados de plano. */ }
      personId = people.some((person) => person.id === requested) ? requested : (people.some((person) => person.id === remembered) ? remembered : people[0].id);
      $('#planPerson').disabled = false; $('#addScheduleDay').disabled = false;
      renderPeople();
      await loadPersonPlans();
      $('#addScheduleDay').disabled = !state;
    } catch (error) {
      setStatus(`${error.message} A página depende do SQL do servidor para ler e salvar.`, 'error');
    }
  }
  init();
})();
