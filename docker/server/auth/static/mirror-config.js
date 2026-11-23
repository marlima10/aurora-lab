(()=>{'use strict';
const $=id=>document.getElementById(id),form=$('settingsForm'),labels={clock:'Data e hora',weather:'Clima local',reminders:'Lembretes',calendar:'Calendário',goals:'Metas de exercícios',history:'Histórico de exercícios',news:'Feed de notícias'},apps={opengym:'openGym',mealie:'Mealie',javis:'Jarvis',reminders:'Lembretes',calendar:'Calendário',manyfold:'Manyfold',actual:'Actual Budget',monitor:'Monitor de processos'};
let state,defaults,session,gallery;
function message(text,kind=''){ $('status').textContent=text;$('status').className=kind;}
async function api(value){const r=await fetch('/auth/mirror/settings',{cache:'no-store',credentials:'same-origin',...(value!==undefined?{method:'POST',headers:{'Content-Type':'application/json','X-Aurora-CSRF':session.csrf},body:JSON.stringify(value)}:{})});const v=await r.json();if(!r.ok)throw Error(v.error||'Não foi possível salvar as configurações.');return v;}
function widgets(){const root=$('widgets');root.replaceChildren();state.order.forEach((key,index)=>{const row=document.createElement('div');row.className='widget';const label=document.createElement('label'),input=document.createElement('input');input.type='checkbox';input.checked=state.widgets[key];input.onchange=()=>{state.widgets[key]=input.checked};label.append(input,document.createTextNode(labels[key]));row.append(label);for(const [delta,caption,icon] of [[-1,'Mover para cima','↑'],[1,'Mover para baixo','↓']]){const b=document.createElement('button');b.type='button';b.textContent=icon;b.setAttribute('aria-label',caption+': '+labels[key]);b.disabled=index+delta<0||index+delta>=state.order.length;b.onclick=()=>{[state.order[index],state.order[index+delta]]=[state.order[index+delta],state.order[index]];widgets();$('widgets').querySelectorAll('.widget')[index+delta].querySelector('button:not(:disabled)')?.focus()};row.append(b)}root.append(row)})}
function draw(){widgets();const root=$('shortcuts');root.replaceChildren();for(const [key,title] of Object.entries(apps)){const label=document.createElement('label');label.className='check';const check=document.createElement('input');check.type='checkbox';check.checked=state.shortcuts[key];check.onchange=()=>{state.shortcuts[key]=check.checked};label.append(check,document.createTextNode(title));root.append(label)}for(const name of ['backgroundDim','panelOpacity','blur','fontScale','refreshMinutes','newsCount']){form.elements[name].value=state[name];if($(name+'Value'))$(name+'Value').textContent=state[name]+(name==='blur'?' px':'%')}form.elements.clock24.checked=state.clock24;form.elements.temperatureUnit.value=state.temperatureUnit;form.elements.backgroundMode.value=state.backgroundMode;form.elements.backgroundSeconds.value=state.backgroundSeconds;renderBackgrounds();form.elements.calendarView.value=state.calendarView;form.elements.holidayRegion.value=state.holidayRegion;form.elements.cityQuery.value=state.weatherLocation?.name||'';$('cityStatus').textContent=state.weatherLocation?'Cidade selecionada: '+state.weatherLocation.name:'Nenhuma cidade salva.';$('cityResults').replaceChildren();form.hidden=false;}
for(const name of ['backgroundDim','panelOpacity','blur','fontScale'])form.elements[name].oninput=e=>{$(name+'Value').textContent=e.target.value+(name==='blur'?' px':'%')};
function renderBackgrounds(){
 const root=$('backgroundGallery');root.replaceChildren();if(!gallery)return;
 for(const image of gallery.images){
  const label=document.createElement('label');label.className='background-choice';
  const check=document.createElement('input');check.type='checkbox';check.checked=state.backgroundImages.includes(image.id);check.setAttribute('aria-label','Selecionar '+image.name);
  check.onchange=()=>{state.backgroundImages=check.checked?[...state.backgroundImages,image.id]:state.backgroundImages.filter(id=>id!==image.id);$('backgroundStatus').textContent=state.backgroundImages.length+' imagem(ns) selecionada(s). Salve para aplicar.';};
  const photo=document.createElement('img');photo.src=image.thumbnail;photo.alt='';photo.loading='lazy';
  const name=document.createElement('span');name.textContent=image.name;label.append(check,photo,name);root.append(label);
 }
 if(!gallery.images.length)root.textContent='Nenhuma imagem enviada. O pôr do sol original continua disponível.';
}
async function loadBackgrounds(){
 const response=await fetch('/auth/mirror/backgrounds',{cache:'no-store',credentials:'same-origin'}),result=await response.json();
 if(!response.ok)throw Error(result.error||'Não foi possível carregar a galeria.');gallery=result;renderBackgrounds();
 $('backgroundStatus').textContent=result.images.length+' imagem(ns) na galeria.'+(result.skipped?' '+result.skipped+' arquivo(s) não disponível(is); confira formato, tamanho e limite.':'');
}
$('refreshBackgrounds').onclick=async()=>{try{await loadBackgrounds()}catch(error){$('backgroundStatus').textContent=error.message}};
$('uploadBackgrounds').onclick=async()=>{
 const files=[...form.elements.backgroundFiles.files];if(!files.length){$('backgroundStatus').textContent='Escolha uma ou mais imagens para enviar.';return}
 if(files.length>50){$('backgroundStatus').textContent='Envie até 50 imagens por vez.';return}
 $('uploadBackgrounds').disabled=true;$('save').disabled=true;$('refreshBackgrounds').disabled=true;
 let sent=0;
 try{
  for(const file of files){
   if(file.size>12*1024*1024)throw Error(file.name+': o limite é 12 MB por foto.');
   const mime=file.type||({'jpg':'image/jpeg','jpeg':'image/jpeg','png':'image/png','webp':'image/webp'}[file.name.split('.').pop().toLowerCase()]);
   if(!['image/jpeg','image/png','image/webp'].includes(mime))throw Error(file.name+': use JPG, PNG ou WebP.');
   $('backgroundStatus').textContent='Enviando '+(sent+1)+' de '+files.length+': '+file.name;
   const response=await fetch('/auth/mirror/backgrounds/upload',{method:'POST',credentials:'same-origin',headers:{'Content-Type':mime,'X-Aurora-CSRF':session.csrf,'X-Image-Name':encodeURIComponent(file.name)},body:file});
   const result=await response.json();if(!response.ok)throw Error(result.error||'Não foi possível enviar '+file.name);
   gallery=result;if(!state.backgroundImages.includes(result.uploadedId))state.backgroundImages.push(result.uploadedId);sent++;renderBackgrounds();
  }
  form.elements.backgroundFiles.value='';$('backgroundStatus').textContent=sent+' imagem(ns) enviada(s) e selecionada(s). Escolha o modo e salve para aplicar.';
 }catch(error){$('backgroundStatus').textContent=error.message+(sent?' '+sent+' imagem(ns) já foram guardadas.':'')}
 finally{$('uploadBackgrounds').disabled=false;$('save').disabled=false;$('refreshBackgrounds').disabled=false}
};
$('searchCity').onclick=async()=>{
 const query=form.elements.cityQuery.value.trim();if(query.length<2){$('cityStatus').textContent='Digite pelo menos dois caracteres.';return}
 $('searchCity').disabled=true;$('cityStatus').textContent='Buscando cidade…';$('cityResults').replaceChildren();
 try{
  const response=await fetch('/auth/mirror/locations',{method:'POST',cache:'no-store',credentials:'same-origin',headers:{'Content-Type':'application/json','X-Aurora-CSRF':session.csrf},body:JSON.stringify({query})});
  const result=await response.json();if(!response.ok)throw Error(result.error||'Não foi possível buscar a cidade.');
  for(const loc of result.locations){const button=document.createElement('button');button.type='button';button.textContent=loc.name;button.onclick=()=>{state.weatherLocation=loc;form.elements.cityQuery.value=loc.name;$('cityResults').replaceChildren();$('cityStatus').textContent='Selecionada: '+loc.name+'. Clique em Salvar configurações para gravar.';};$('cityResults').append(button)}
  $('cityStatus').textContent=result.locations.length?'Escolha a cidade na lista abaixo.':'Cidade não encontrada. Tente o nome seguido do estado.';
 }catch(error){$('cityStatus').textContent=error.message}finally{$('searchCity').disabled=false}
};
$('restoreDefaults').onclick=()=>{state=structuredClone(defaults);draw();message('Padrão carregado no formulário. Clique em Salvar configurações para aplicar.');};
form.onsubmit=async event=>{event.preventDefault();if(!Object.values(state.widgets).some(Boolean)){message('Mantenha pelo menos um bloco visível.','error');return}$('save').disabled=true;message('Salvando…');for(const name of ['backgroundDim','panelOpacity','blur','fontScale','refreshMinutes','newsCount'])state[name]=Number(form.elements[name].value);state.clock24=form.elements.clock24.checked;state.temperatureUnit=form.elements.temperatureUnit.value;state.backgroundMode=form.elements.backgroundMode.value;state.backgroundSeconds=Number(form.elements.backgroundSeconds.value);state.calendarView=form.elements.calendarView.value;state.holidayRegion=form.elements.holidayRegion.value;try{const v=await api(state);state=v.settings;defaults=v.defaults;draw();try{localStorage.setItem('aurora.mirror.settings.updated',String(Date.now()))}catch(_){}message('Configurações salvas. A tela inicial será atualizada na próxima consulta; use Ver tela inicial para conferir agora.','success');}catch(e){message(e.message,'error')}finally{$('save').disabled=false}};
(async()=>{try{const r=await fetch('/auth/session',{cache:'no-store',credentials:'same-origin'});if(!r.ok)throw Error('Entre com sua conta de administrador.');session=await r.json();if(!session.admin)throw Error('Somente o administrador pode configurar a tela.');const v=await api();state=v.settings;defaults=v.defaults;draw();await loadBackgrounds();message('Ajustes carregados. Altere as opções e salve para aplicar.');}catch(e){message(e.message,'error')}})();
})();
