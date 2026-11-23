import fs from 'node:fs';import vm from 'node:vm';import assert from 'node:assert/strict';
const window={};vm.runInNewContext(fs.readFileSync(process.argv[2]+'/docker/server/mirror/MMM-Aurora/backgrounds.js','utf8'),{window});
const photos=[],timers=[],style={};let visibility;
class FakeImage{constructor(){photos.push(this)}set src(url){this.url=url}}
const doc={hidden:false,addEventListener:(name,fn)=>{visibility=fn},removeEventListener(){}};
const root={style:{setProperty:(k,v)=>{style[k]=v},removeProperty:k=>{delete style[k]}}};
const env={Image:FakeImage,document:doc,setTimeout:(fn,ms)=>{timers.push({fn,ms});return timers.length},clearTimeout(){}};
const backgrounds=new window.AuroraMirrorBackgrounds(root,env),a='a'.repeat(64),b='b'.repeat(64);
const prefs={backgroundMode:'slideshow',backgroundImages:[a,b],backgroundSeconds:30};
backgrounds.configure(prefs);assert.equal(style['--mirror-background'],undefined);photos.at(-1).onload();assert(style['--mirror-background'].includes(a));assert.equal(timers.at(-1).ms,30000);
const count=photos.length;backgrounds.configure(prefs);assert.equal(photos.length,count);
timers.at(-1).fn();assert(style['--mirror-background'].includes(a));photos.at(-1).onload();assert(style['--mirror-background'].includes(b));
doc.hidden=true;visibility();const length=timers.length;backgrounds.schedule();assert.equal(timers.length,length);doc.hidden=false;visibility();assert.equal(timers.length,length+1);
backgrounds.configure({backgroundMode:'fixed',backgroundImages:[a],backgroundSeconds:30});const stale=photos.at(-1);
backgrounds.configure({backgroundMode:'default',backgroundImages:[],backgroundSeconds:60});stale.onload();assert.equal(style['--mirror-background'],undefined);
backgrounds.configure(prefs);photos.at(-1).onerror();photos.at(-1).onerror();assert.equal(style['--mirror-background'],undefined);
backgrounds.destroy();
console.log('Slideshow order, preloading, interval, hidden-tab pause, stale-load cancellation, missing-image fallback and original background passed.');
