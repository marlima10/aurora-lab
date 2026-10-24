(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const number = (n, digits = 1) => typeof n === 'number' && Number.isFinite(n) ? n.toLocaleString('pt-BR', { maximumFractionDigits: digits, minimumFractionDigits: digits }) : '—';
  const money = n => Number.isFinite(n) ? n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' }) : '—';
  const profiles = { eco: 'Economia máxima', balanced: 'Equilibrado', performance: 'Desempenho', custom: 'Personalizado' };
  const statusNames = { Discharging: 'Na bateria', Charging: 'Carregando', Full: 'Carga completa', 'Not charging': 'Na tomada', Unknown: 'Estado indisponível' };
  let latest = null, loading = false, lastFocus = null, adminKey = '';
  const configKey = 'aurora.energy.estimate.v1';
  const formFields = ['powerTariff', 'powerAwake', 'powerSleep', 'powerNightHours'];
  let preferences = {};
  try { preferences = JSON.parse(localStorage.getItem(configKey) || '{}'); } catch (_) { /* Start with editable empty values. */ }
  formFields.forEach(id => {
    if (preferences[id] !== undefined) $(id).value = preferences[id];
    $(id).addEventListener('input', updateCost);
  });
  function numericInput(id) {
    const value = $(id).value.trim();
    if (!value) return null;
    const n = Number(value);
    return Number.isFinite(n) ? n : null;
  }
  function updateCost() {
    const tariff = numericInput('powerTariff'), awake = numericInput('powerAwake'), sleep = numericInput('powerSleep'), hours = numericInput('powerNightHours');
    const validWatts = awake !== null && awake >= 0 && awake <= 10000;
    const validNight = sleep !== null && sleep >= 0 && sleep <= 10000 && hours !== null && hours >= 0 && hours <= 24;
    const kwh24 = validWatts ? awake * 24 * 30 / 1000 : null;
    const kwhNight = validWatts && validNight ? (awake * (24 - hours) + sleep * hours) * 30 / 1000 : null;
    const validTariff = tariff !== null && tariff >= 0 && tariff <= 100;
    $('powerCost24').textContent = kwh24 !== null && validTariff ? money(kwh24 * tariff) : '—';
    $('powerKwh24').textContent = kwh24 !== null ? number(kwh24, 2) + ' kWh / 30 dias' : 'Informe a potência em watts';
    $('powerCostNight').textContent = kwhNight !== null && validTariff ? money(kwhNight * tariff) : '—';
    $('powerKwhNight').textContent = kwhNight !== null ? number(kwhNight, 2) + ' kWh / 30 dias' : 'Preencha os parâmetros';
    const difference = kwh24 !== null && kwhNight !== null ? kwh24 - kwhNight : null;
    $('powerSavings').textContent = difference !== null && validTariff ? money(difference * tariff) : '—';
    $('powerSavingsKwh').textContent = difference !== null ? number(difference, 2) + ' kWh / 30 dias' : 'Comparação estimada';
    $('powerCostNote').textContent = !validWatts ? 'Informe a potência medida na tomada. Você também pode simular com a leitura de descarga da bateria, sem tratá-la como medição da tomada.' : !validTariff ? 'Informe a tarifa em R$/kWh para calcular os valores. O consumo em kWh já foi calculado.' : !validNight ? 'A tarifa e as potências devem ser positivas; as horas devem estar entre 0 e 24.' : 'Simulação de 30 dias. Não é uma conta medida. Suspensão noturna não está ativada.';
    if (latest) renderEnergy(latest);
    preferences = Object.fromEntries(formFields.map(id => [id, $(id).value]));
    try { localStorage.setItem(configKey, JSON.stringify(preferences)); } catch (_) { /* Values remain usable in this tab. */ }
  }
  function setValue(id, value, unit = '') {
    $(id).textContent = typeof value === 'number' && Number.isFinite(value) ? number(value) + unit : 'Indisponível';
  }
  function gpuRows(gpus) {
    const list = $('powerGpuList');
    list.replaceChildren();
    if (!gpus.length) { list.textContent = 'Nenhuma GPU detectada pelo monitor.'; return; }
    gpus.forEach(gpu => {
      const row = document.createElement('div'); row.className = 'gpu-item';
      const heading = document.createElement('div'); heading.className = 'gpu-heading';
      const name = document.createElement('strong'); name.textContent = gpu.name;
      const badge = document.createElement('span'); badge.className = 'power-status'; badge.textContent = gpu.runtime_status === 'suspended' ? 'Suspensa' : gpu.runtime_status === 'active' ? 'Ativa' : 'Estado indisponível';
      heading.append(name, badge); row.append(heading);
      const metrics = document.createElement('div'); metrics.className = 'gpu-metrics';
      [['Potência', gpu.power_w, ' W'], ['Utilização', gpu.utilization_percent, '%'], ['Temperatura', gpu.temperature_c, ' °C']].forEach(([label, value, unit]) => {
        const item = document.createElement('div'), valueEl = document.createElement('b'), labelEl = document.createElement('span');
        valueEl.textContent = typeof value === 'number' ? number(value) + unit : '—'; labelEl.textContent = label;
        item.append(valueEl, labelEl); metrics.append(item);
      });
      row.append(metrics);
      const note = document.createElement('p'); note.textContent = gpu.reason || (gpu.power_source ? gpu.power_source + ' · não somar ao pacote CPU.' : 'Dados fornecidos pelo driver.'); row.append(note);
      const driver = document.createElement('p'); driver.textContent = 'Driver: ' + gpu.driver; row.append(driver); list.append(row);
    });
  }
  function renderChart(samples) {
    const svg = $('powerChart'); svg.replaceChildren();
    const NS = 'http://www.w3.org/2000/svg';
    const add = (tag, attributes, text) => { const el = document.createElementNS(NS, tag); Object.entries(attributes).forEach(([k, v]) => el.setAttribute(k, String(v))); if (text) el.textContent = text; svg.append(el); return el; };
    const rows = samples.slice(-90), values = rows.flatMap(r => [r.cpu_w, r.battery_w]).filter(v => typeof v === 'number' && Number.isFinite(v));
    if (!values.length || rows.length < 2) { $('powerChartEmpty').hidden = false; return; }
    $('powerChartEmpty').hidden = true;
    const max = Math.max(5, Math.ceil(Math.max(...values) / 5) * 5);
    [0, .5, 1].forEach(part => { const y = 125 - 110 * part; add('line', { x1: 34, y1: y, x2: 580, y2: y, stroke: 'var(--line)', 'stroke-width': 1 }); add('text', { x: 0, y: y + 4 }, number(max * part, 0) + ' W'); });
    [['battery_w', 'var(--cyan)'], ['cpu_w', 'var(--purple)']].forEach(([key, color]) => {
      let points = [];
      const flush = () => { if (points.length > 1) add('polyline', { points: points.join(' '), fill: 'none', stroke: color, 'stroke-width': 2.5, 'vector-effect': 'non-scaling-stroke' }); points = []; };
      rows.forEach((row, i) => { if (typeof row[key] !== 'number' || !Number.isFinite(row[key]) || (i && Date.parse(row.time) - Date.parse(rows[i - 1].time) > 90000)) { flush(); if (typeof row[key] !== 'number') return; } points.push((34 + i * 546 / (rows.length - 1)).toFixed(1) + ',' + (125 - row[key] / max * 110).toFixed(1)); }); flush();
    });
  }
  function renderEnergy(data) {
    const rows = data.daily_energy || [], tariff=numericInput('powerTariff'), valid=tariff !== null && tariff >= 0 && tariff <= 100;
    const now = new Intl.DateTimeFormat('sv-SE',{timeZone:'America/Sao_Paulo'}).format(new Date()), month=now.slice(0,7);
    const current=rows.filter(r=>r.day.startsWith(month)), kwh=current.reduce((n,r)=>n+(r.cpu_seconds>0?r.cpu_kwh:0),0), hours=current.reduce((n,r)=>n+r.cpu_seconds/3600,0);
    $('energyMonth').textContent='Mês '+month.split('-').reverse().join('/')+': CPU '+(hours>0?number(kwh,5)+' kWh em '+number(hours,1)+' h observadas':'sem medição disponível')+(hours>0 && valid?' · custo parcial '+money(kwh*tariff):' · informe a tarifa para calcular o custo')+'. Cobertura parcial; não é medição da tomada.';
    $('energyDaily').replaceChildren();
    for(const row of [...rows].reverse()){
      const tr=document.createElement('tr');
      for(const value of [row.day.split('-').reverse().join('/'),row.cpu_seconds>0?number(row.cpu_kwh,5):'—',row.cpu_seconds>0?number(row.cpu_seconds/3600,2):'—',row.battery_seconds>0?number(row.battery_discharge_kwh,5):'—',row.battery_seconds>0?number(row.battery_seconds/3600,2):'—',row.cpu_seconds>0 && valid?money(row.cpu_kwh*tariff):'—']){const td=document.createElement('td');td.textContent=value;tr.append(td);}
      $('energyDaily').append(tr);
    }
  }
  function render(data) {
    latest = data;
    renderEnergy(data);
    const battery = data.battery || {}, controls = data.controls || {}, cpu = data.cpu || {}, observed = data.observed || {};
    $('powerLive').textContent = 'Atualizado às ' + new Date(data.generated).toLocaleTimeString('pt-BR');
    $('powerBatteryPercent').textContent = battery.present ? number(battery.percent, 0) + '%' : 'Sem bateria';
    $('powerBatteryButton').dataset.low = String(battery.present && battery.percent < 20);
    $('powerBatteryState').textContent = battery.present ? statusNames[battery.status] || battery.status : 'Ver opções de energia';
    const discharging = battery.status === 'Discharging';
    setValue('powerDraw', discharging ? battery.power_w : null, ' W');
    $('powerDrawSource').textContent = discharging ? 'Descarga da bateria · não mede a tomada' : battery.status === 'Charging' ? 'Bateria carregando · consumo da tomada não medido' : 'Consumo da tomada não medido';
    setValue('powerCpu', cpu.power_w, ' W');
    $('powerProfile').textContent = profiles[controls.profile] || 'Indisponível';
    $('powerProfileSub').textContent = controls.manager ? 'Gerenciado por ' + controls.manager : 'Clique na bateria para configurar';
    $('powerObserved').textContent = number(observed.cpu_kwh, 4) + ' kWh';
    $('powerCoverage').textContent = 'Pacote CPU hoje · ' + number((observed.cpu_seconds || 0) / 3600, 1) + ' h observadas';
    $('powerHealth').textContent = number(battery.health_percent, 0) + '%';
    $('powerAutonomy').textContent = battery.estimated_hours !== null && battery.estimated_hours !== undefined ? number(battery.estimated_hours, 1) + ' h' : '—';
    $('powerCycles').textContent = number(battery.cycles, 0);
    $('powerModalBattery').textContent = battery.present ? number(battery.percent, 0) + '% · ' + (statusNames[battery.status] || battery.status) : 'Sem bateria detectada';
    $('powerEstimateFromBattery').disabled = !(discharging && typeof battery.power_w === 'number');
    gpuRows(data.gpus || []); renderChart(data.history || []);
    if (!$('powerDialog').open) syncControls(controls);
  }
  function syncControls(controls) {
    document.querySelectorAll('input[name="powerProfileChoice"]').forEach(radio => { radio.disabled = !controls.profiles_available; radio.checked = radio.value === controls.profile; });
    $('powerBrightness').disabled = !controls.brightness_available;
    $('powerBrightness').value = controls.brightness_percent ?? 50;
    $('powerBrightnessValue').textContent = number(controls.brightness_percent, 0) + '%';
    $('powerApply').disabled = !controls.profiles_available && !controls.brightness_available;
    $('powerControlNote').textContent = controls.manager ? 'Outro gerenciador está ativo: os perfis de CPU ficam bloqueados para evitar conflito.' : 'Economia máxima reduz os picos da CPU e desativa o turbo. Rede, Docker e USB permanecem ativos.';
  }
  async function refresh() {
    if (document.hidden || loading) return;
    loading = true;
    try {
      const response = await fetch('/api/power', { cache: 'no-store', signal: AbortSignal.timeout(8000) });
      if (!response.ok) throw Error('offline');
      const data = await response.json();
      if (!data.generated || !Number.isFinite(Date.parse(data.generated)) || Date.now() - Date.parse(data.generated) > 30000) throw Error('stale');
      render(data);
    } catch (_) {
      latest = null;
      $('powerLive').textContent = 'Monitor de energia indisponível';
      $('powerBatteryPercent').textContent = '—'; $('powerBatteryState').textContent = 'Dados indisponíveis';
      ['powerDraw', 'powerCpu', 'powerObserved', 'powerProfile'].forEach(id => { $(id).textContent = '—'; });
      $('powerDrawSource').textContent = 'Sem leitura atual'; $('powerCoverage').textContent = 'Aguardando monitor';
      $('powerProfileSub').textContent = 'Controles indisponíveis'; $('powerApply').disabled = true;
      $('powerEstimateFromBattery').disabled = true;
      ['powerHealth', 'powerAutonomy', 'powerCycles', 'powerModalBattery'].forEach(id => { $(id).textContent = '—'; });
      $('powerGpuList').textContent = 'Sem dados atuais das GPUs.';
      $('powerChart').replaceChildren(); $('powerChartEmpty').hidden = false;
    } finally { loading = false; }
  }
  function openDialog() {
    lastFocus = document.activeElement;
    if (latest) syncControls(latest.controls || {});
    else { document.querySelectorAll('input[name="powerProfileChoice"]').forEach(r => { r.disabled = true; }); $('powerBrightness').disabled = true; }
    $('powerFeedback').textContent = ''; $('powerAdminKey').value = '';
    $('powerDialog').showModal();
  }
  $('powerBatteryButton').addEventListener('click', openDialog);
  $('powerSettingsButton').addEventListener('click', openDialog);
  $('powerClose').addEventListener('click', () => $('powerDialog').close());
  $('powerCancel').addEventListener('click', () => $('powerDialog').close());
  $('powerDialog').addEventListener('close', () => { $('powerAdminKey').value = ''; lastFocus?.focus(); });
  $('powerDialog').addEventListener('click', event => { if (event.target !== $('powerDialog')) return; const rect = $('powerDialog').getBoundingClientRect(); if (event.clientX < rect.left || event.clientX > rect.right || event.clientY < rect.top || event.clientY > rect.bottom) $('powerDialog').close(); });
  $('powerBrightness').addEventListener('input', () => { $('powerBrightnessValue').textContent = $('powerBrightness').value + '%'; });
  $('powerEstimateFromBattery').addEventListener('click', () => { if (latest?.battery?.status === 'Discharging') { $('powerAwake').value = latest.battery.power_w.toFixed(1); updateCost(); } });
  $('powerSettingsForm').addEventListener('submit', async event => {
    event.preventDefault();
    if (!latest) return;
    const feedback = $('powerFeedback'), key = $('powerAdminKey').value.trim() || adminKey;
    if (!key) { feedback.dataset.state = 'error'; feedback.textContent = 'Informe a chave administrativa do painel para aplicar alterações.'; $('powerAdminKey').focus(); return; }
    const controls = latest.controls || {}, payload = {};
    const selected = document.querySelector('input[name="powerProfileChoice"]:checked');
    if (controls.profiles_available && selected) payload.profile = selected.value;
    if (controls.brightness_available) payload.brightness_percent = Number($('powerBrightness').value);
    if (!Object.keys(payload).length) return;
    $('powerApply').disabled = true; feedback.dataset.state = ''; feedback.textContent = 'Aplicando configurações…';
    try {
      const response = await fetch('/api/power/settings', { method: 'POST', headers: { 'Content-Type': 'application/json', Authorization: 'Bearer ' + key }, body: JSON.stringify(payload), signal: AbortSignal.timeout(15000) });
      const data = await response.json();
      if (!response.ok || !data.ok) { if (response.status === 401) adminKey = ''; throw Error(data.error || 'Não foi possível aplicar.'); }
      adminKey = key; $('powerAdminKey').value = ''; latest.controls = data.controls; syncControls(data.controls);
      feedback.dataset.state = 'ok'; feedback.textContent = 'Configurações aplicadas no servidor e salvas para as próximas inicializações.';
      await refresh();
    } catch (error) { feedback.dataset.state = 'error'; feedback.textContent = error.message === 'Failed to fetch' ? 'Falha de conexão. Confira o estado do servidor antes de tentar novamente.' : error.message; }
    finally { if (latest) $('powerApply').disabled = false; }
  });
  document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
  updateCost(); refresh(); setInterval(refresh, 10000);
})();
