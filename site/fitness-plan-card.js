(() => {
  const $ = (selector) => document.querySelector(selector);
  const dayNames = ['domingo', 'segunda-feira', 'terça-feira', 'quarta-feira', 'quinta-feira', 'sexta-feira', 'sábado'];
  const message = $('#plannedWorkoutMessage');
  const items = $('#plannedWorkoutExercises');
  const open = $('#openTrainingPlans');
  const start = $('#startPlannedWorkout');
  const personSelect = $('#personFilter');
  if (!message || !personSelect) return;

  function disableStart() {
    if (start) {
      start.disabled = true;
      start._fitnessPlan = null;
      start._fitnessPersonId = '';
    }
  }

  async function refresh() {
    const personId = personSelect.value;
    items.replaceChildren();
    if (!personId || personId === 'all') {
      disableStart();
      message.textContent = 'Escolha um perfil para consultar a agenda semanal.';
      open.href = '/fitness-planos.html';
      return;
    }
    open.href = '/fitness-planos.html?person=' + encodeURIComponent(personId);
    try {
      const response = await fetch('/fitness-api?action=plans&person=' + encodeURIComponent(personId), { cache: 'no-store' });
      const data = await response.json();
      if (!response.ok || !data.ok || !data.personExists) throw new Error(data.error || 'Perfil indisponível no SQL');
      if (!data.schedule.length) {
        disableStart();
        message.textContent = 'Este perfil ainda não tem dias de treino planejados.';
        return;
      }
      const today = new Date().getDay();
      const slot = data.schedule.find((item) => item.weekday === today) || data.schedule.slice().sort((a, b) => ((a.weekday - today + 7) % 7) - ((b.weekday - today + 7) % 7))[0];
      const plan = data.plans.find((item) => item.code === slot.planCode);
      if (start) {
        start.disabled = !plan?.exercises?.length;
        start._fitnessPlan = plan || null;
        start._fitnessPersonId = personId;
      }
      const personName = personSelect.selectedOptions[0]?.textContent || 'Perfil';
      const isToday = slot.weekday === today;
      const time = slot.time ? ' · ' + slot.time : '';
      message.textContent = `${personName} · ${isToday ? 'Hoje' : 'Próximo: ' + dayNames[slot.weekday]} · Treino ${slot.planCode} (${plan?.name || 'sem título'})${time}`;
      (plan?.exercises || []).slice(0, 4).forEach((exercise) => {
        const tag = document.createElement('span');
        tag.textContent = exercise.mode === 'cardio' ? `${exercise.name} · ${exercise.durationMinutes} min` : `${exercise.name} · ${exercise.sets}×${exercise.reps}`;
        items.append(tag);
      });
      if (!plan?.exercises?.length) {
        const tag = document.createElement('span');
        tag.textContent = 'Ficha sem exercícios cadastrados';
        items.append(tag);
      }
    } catch (error) {
      disableStart();
      message.textContent = 'Não foi possível consultar a agenda no banco SQL. Verifique a conexão com o Armbian.';
    }
  }

  start?.addEventListener('click', () => {
    if (!start._fitnessPlan || start.disabled) return;
    window.dispatchEvent(new CustomEvent('fitness:start-guided-workout', {
      detail: { personId: start._fitnessPersonId, plan: start._fitnessPlan },
    }));
  });

  personSelect.addEventListener('change', refresh);
  new MutationObserver(refresh).observe(personSelect, { childList: true });
  refresh();
})();
