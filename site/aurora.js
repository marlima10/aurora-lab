const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function json(url){let r=await fetch(url+(url.includes('?')?'&':'?')+'t='+Date.now(),{cache:'no-store'});if(!r.ok)throw Error(url+' HTTP '+r.status);return r.json()}
function age(iso){let n=Date.now()-Date.parse(iso);if(!isFinite(n))return '--';let s=Math.max(0,Math.floor(n/1000));return s<60?s+'s':Math.floor(s/60)+'min'}
function openPort(p,path=''){window.open(location.protocol+'//'+location.hostname+':'+p+path,'_blank')}
document.addEventListener('visibilitychange',()=>{document.querySelectorAll('[data-stream]').forEach(i=>{if(document.hidden){i.dataset.src=i.src;i.src=''}else if(i.dataset.src)i.src=i.dataset.src})})
