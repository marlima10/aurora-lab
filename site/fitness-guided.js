(() => {
  const $ = (selector) => document.querySelector(selector);
  const modal = $('#guidedWorkoutModal');
  if (!modal) return;

  let session = null;
  let elapsedTimer = null;
  let restTimer = null;
  let restRemaining = 90;

  const localDay = () => {
    const now = new Date();
    return new Date(now.getTime() - now.getTimezoneOffset() * 60000).toISOString().slice(0, 10);
  };
  const mmss = (seconds) => `${String(Math.floor(seconds / 60)).padStart(2, '0')}:${String(seconds % 60).padStart(2, '0')}`;
  const elapsedSeconds = () => session ? Math.max(0, Math.floor((Date.now() - session.startedAt) / 1000)) : 0;
  const toast = (message) => {
    const node = $('#toast');
    if (!node) return;
    node.textContent = message;
    node.classList.add('show');
    setTimeout(() => node.classList.remove('show'), 2600);
  };

  function stopTimers() {
    clearInterval(elapsedTimer);
    clearInterval(restTimer);
    elapsedTimer = null;
    restTimer = null;
  }

  function renderList() {
    const list = $('#guidedExerciseList');
    list.replaceChildren();
    session.plan.exercises.forEach((exercise, index) => {
      const item = document.createElement('li');
      if (index === session.index) item.classList.add('active');
      if (session.progress[index].completed) item.classList.add('done');
      const number = document.createElement('span');
      number.className = 'guided-exercise-index';
      number.textContent = session.progress[index].completed ? '✓' : String(index + 1);
      const copy = document.createElement('span');
      copy.textContent = exercise.name;
      item.append(number, copy);
      list.append(item);
    });
  }

  function render() {
    if (!session) return;
    const exercises = session.plan.exercises;
    const finished = session.index >= exercises.length;
    const exercise = exercises[session.index];
    const progress = session.progress;
    const completeCount = progress.filter((item) => item.completed).length;
    $('#guidedPlanTitle').textContent = `Treino ${session.plan.code} · ${session.plan.name}`;
    $('#guidedExerciseCount').textContent = finished ? 'Treino concluído' : `Exercício ${session.index + 1} de ${exercises.length}`;
    $('#guidedProgress').style.width = `${Math.round((completeCount / exercises.length) * 100)}%`;
    $('#guidedElapsed').textContent = mmss(elapsedSeconds());
    $('#guidedFinishedMessage').hidden = !finished;
    $('#guidedSummary').hidden = !finished;
    $('#guidedCompleteButton').hidden = finished;
    $('#guidedRestButton').hidden = finished;
    if (finished) {
      $('#guidedMuscle').textContent = 'SESSÃO COMPLETA';
      $('#guidedExerciseName').textContent = 'Bom trabalho!';
      $('#guidedPrescription').textContent = `${completeCount} exercício${completeCount === 1 ? '' : 's'} concluído${completeCount === 1 ? '' : 's'}. Revise os dados e salve no banco.`;
      $('#guidedSetLabel').textContent = 'Tempo total';
      $('#guidedSetValue').textContent = mmss(elapsedSeconds());
      $('#guidedRestClock').textContent = '—';
    } else {
      const current = progress[session.index];
      const cardio = exercise.mode === 'cardio';
      $('#guidedMuscle').textContent = exercise.muscleGroup || (cardio ? 'CARDIO' : 'EXERCÍCIO');
      $('#guidedExerciseName').textContent = exercise.name;
      $('#guidedPrescription').textContent = cardio
        ? `Tempo planejado: ${Number(exercise.durationMinutes) || 0} minutos`
        : `${Number(exercise.sets) || 1} séries · ${Number(exercise.reps) || 0} repetições`;
      $('#guidedSetLabel').textContent = cardio ? 'Duração planejada' : 'Série atual';
      $('#guidedSetValue').textContent = cardio
        ? `${Number(exercise.durationMinutes) || 0} min`
        : `${current.setsDone + 1} / ${Number(exercise.sets) || 1}`;
      $('#guidedCompleteButton').textContent = cardio ? 'Concluir cardio' : 'Concluir série';
      $('#guidedRestButton').textContent = restTimer ? `Pular descanso (${mmss(restRemaining)})` : '⏱ Descansar 90 s';
      $('#guidedRestClock').textContent = restTimer ? mmss(restRemaining) : '01:30';
    }
    renderList();
  }

  function beginRest() {
    clearInterval(restTimer);
    restRemaining = 90;
    restTimer = setInterval(() => {
      restRemaining -= 1;
      if (restRemaining <= 0) {
        clearInterval(restTimer);
        restTimer = null;
        restRemaining = 0;
      }
      render();
    }, 1000);
    render();
  }

  function start(detail) {
    if (!window.fitnessCanSaveToSql?.()) {
      alert('O banco SQL do Armbian está indisponível. Aguarde a sincronização antes de iniciar um treino guiado.');
      return;
    }
    const plan = detail?.plan;
    if (!plan?.exercises?.length) {
      toast('Essa ficha ainda não tem exercícios cadastrados.');
      return;
    }
    stopTimers();
    session = {
      sessionId: window.crypto?.randomUUID ? window.crypto.randomUUID() : `guided-${Date.now()}-${Math.random().toString(36).slice(2)}`,
      personId: detail.personId,
      date: localDay(),
      plan: JSON.parse(JSON.stringify(plan)),
      index: 0,
      startedAt: Date.now(),
      progress: plan.exercises.map(() => ({ setsDone: 0, completed: false })),
    };
    $('#guidedDistance').value = '';
    $('#guidedCalories').value = '';
    $('#guidedSave').disabled = false;
    modal.classList.add('show');
    render();
    elapsedTimer = setInterval(() => {
      if (session) {
        $('#guidedElapsed').textContent = mmss(elapsedSeconds());
        if (session.index >= session.plan.exercises.length) $('#guidedSetValue').textContent = mmss(elapsedSeconds());
      }
    }, 1000);
  }

  $('#guidedCompleteButton').addEventListener('click', () => {
    if (!session) return;
    clearInterval(restTimer);
    restTimer = null;
    const exercise = session.plan.exercises[session.index];
    const current = session.progress[session.index];
    if (exercise.mode === 'cardio') {
      current.completed = true;
    } else {
      current.setsDone += 1;
      if (current.setsDone >= (Number(exercise.sets) || 1)) current.completed = true;
      else beginRest();
    }
    if (current.completed) session.index += 1;
    render();
  });

  $('#guidedRestButton').addEventListener('click', () => {
    if (!session) return;
    if (restTimer) {
      clearInterval(restTimer);
      restTimer = null;
      restRemaining = 90;
      render();
    } else beginRest();
  });

  $('#guidedSave').addEventListener('click', () => {
    if (!session || session.progress.some((item) => !item.completed)) return;
    if (!window.fitnessCanSaveToSql?.()) {
      alert('O banco SQL ficou indisponível. Reconecte ao portal e tente salvar novamente.');
      return;
    }
    const elapsed = Math.max(60, elapsedSeconds());
    const result = {
      sessionId: session.sessionId,
      personId: session.personId,
      date: session.date,
      planCode: session.plan.code,
      planName: session.plan.name,
      durationMinutes: Math.max(1, Math.round(elapsed / 60)),
      distance: Number($('#guidedDistance').value) || 0,
      calories: Number($('#guidedCalories').value) || 0,
      exercises: session.plan.exercises.map((exercise, index) => ({
        id: exercise.id,
        catalogId: exercise.catalogId,
        name: exercise.name,
        muscleGroup: exercise.muscleGroup,
        mode: exercise.mode,
        setsPlanned: Number(exercise.sets) || null,
        repsPlanned: Number(exercise.reps) || null,
        durationMinutesPlanned: Number(exercise.durationMinutes) || null,
        setsCompleted: session.progress[index].setsDone,
        completed: session.progress[index].completed,
      })),
    };
    $('#guidedSave').disabled = true;
    window.dispatchEvent(new CustomEvent('fitness:guided-complete', { detail: result }));
    stopTimers();
    session = null;
    modal.classList.remove('show');
  });

  function closeSession() {
    if (!session) {
      modal.classList.remove('show');
      return;
    }
    if (!confirm('Sair do treino guiado? O progresso desta sessão ainda não foi gravado.')) return;
    stopTimers();
    session = null;
    modal.classList.remove('show');
  }

  $('#guidedClose').addEventListener('click', closeSession);
  modal.addEventListener('click', (event) => {
    if (event.target === modal) closeSession();
  });
  window.addEventListener('fitness:start-guided-workout', (event) => start(event.detail));
})();
