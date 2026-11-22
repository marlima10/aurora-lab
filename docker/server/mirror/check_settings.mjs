import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
let definition;
vm.runInNewContext(fs.readFileSync(process.argv[2]+'/docker/server/mirror/MMM-Aurora/MMM-Aurora.js','utf8'),{Module:{register:(name,body)=>{definition=body}}});
assert.equal(definition.temperature.call({state:{settings:{temperatureUnit:'F'}}},0),32);
assert.equal(definition.temperature.call({state:{settings:{temperatureUnit:'C'}}},23.7),24);
const visible={},order=[],css={},hidden=[];
const root={querySelector:selector=>selector==='[data-widget="clock"]'?visible.clock:selector==='.mirror-grid'?{insertBefore:node=>order.push(node.key)}:selector==='.dock'?{}:Object.values(visible).find(n=>selector.includes('"'+n.key+'"')),
 querySelectorAll:()=>hidden,style:{setProperty:(key,value)=>{css[key]=value}},classList:{toggle:(name,value)=>{root.custom=value}}};
const widgets=['clock','weather','reminders','calendar','goals','history','news'];for(const key of widgets)visible[key]={key};
hidden.push({dataset:{app:'actual',shortcut:'actual'},hasAttribute:()=>false},{dataset:{shortcut:'javis'},hasAttribute:()=>true});
const prefs={order:[...widgets].reverse(),widgets:Object.fromEntries(widgets.map(k=>[k,k!=='weather'])),shortcuts:{actual:true,javis:true},fontScale:110,backgroundDim:50,panelOpacity:40,blur:9,refreshMinutes:5};
const context={root,state:{settings:prefs},session:{admin:false,grants:{}},refreshMinutes:5,tick(){},coords:{lat:1}};
definition.applySettings.call(context);
assert.equal(order.join(),prefs.order.join());assert.equal(visible.weather.hidden,true);assert(hidden.every(x=>x.hidden));assert.equal(css['--mirror-scale'],1.1);assert.equal(context.coords,null);assert(root.custom);
console.log('Settings render in saved order, retain permission checks, hide blocks and apply numeric preferences.');
