/* Saved image IDs only. Load first, then switch; a failed photo never clears the screen. */
(()=>{
 class Backgrounds {
  constructor(root,env={}){
   this.root=root;this.Image=env.Image||window.Image;this.doc=env.document||document;
   this.setTimer=env.setTimeout||((fn,ms)=>setTimeout(fn,ms));this.clearTimer=env.clearTimeout||(id=>clearTimeout(id));
   this.generation=0;this.timer=null;this.index=-1;this.current=null;
   this.visibility=()=>{this.clearTimer(this.timer);if(!this.doc.hidden)this.schedule()};
   this.doc.addEventListener('visibilitychange',this.visibility);
  }
  configure(prefs){
   const mode=prefs.backgroundMode||'default',ids=(prefs.backgroundImages||[]).filter(id=>/^[a-f0-9]{64}$/.test(id));
   const seconds=Number.isInteger(prefs.backgroundSeconds)?Math.min(3600,Math.max(15,prefs.backgroundSeconds)):60;
   const signature=JSON.stringify([mode,ids,seconds]);if(signature===this.signature)return;
   this.signature=signature;this.mode=mode;this.ids=ids;this.seconds=seconds;this.index=-1;this.current=null;this.generation++;this.clearTimer(this.timer);
   if(mode==='default'||!ids.length){this.current=null;this.root.style.removeProperty('--mirror-background');return}
   this.next();
  }
  next(attempt=0){
   if(!this.ids?.length||attempt>=this.ids.length){if(!this.current)this.root.style.removeProperty('--mirror-background');this.schedule();return}
   const generation=this.generation;this.index=(this.index+1)%this.ids.length;
   const url='/auth/mirror/backgrounds/'+this.ids[this.index],image=new this.Image();
   image.onload=()=>{if(generation!==this.generation)return;this.current=url;this.root.style.setProperty('--mirror-background','url("'+url+'")');this.schedule()};
   image.onerror=()=>{if(generation===this.generation)this.next(attempt+1)};
   image.src=url;
  }
  schedule(){this.clearTimer(this.timer);if(this.mode==='slideshow'&&this.ids?.length>1&&!this.doc.hidden)this.timer=this.setTimer(()=>this.next(),this.seconds*1000)}
  destroy(){this.generation++;this.clearTimer(this.timer);this.doc.removeEventListener('visibilitychange',this.visibility)}
 }
 window.AuroraMirrorBackgrounds=Backgrounds;
})();
