import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {nativeSet} from './convert.mjs';
import {PrismaClient} from '@prisma/client';
if(new URL(process.env.DATABASE_URL).pathname!=='/workoutcool_test'||process.env.AURORA_LAB_SSO!=='1')throw Error('Import only into the isolated test database.');
const prisma=new PrismaClient(),raw=fs.readFileSync('/import/source-opengym.json','utf8'),hash=createHash('sha256').update(raw).digest('hex');
const state=JSON.parse(raw).state,catalogue=JSON.parse(fs.readFileSync('/import/catalogue.json','utf8'));
const stable=(kind,value)=>'aurora-'+kind+'-'+createHash('sha256').update(String(value)).digest('hex').slice(0,24);
const userId='aurora-rafael-lab',userEmail='rafael@workoutcool.test';
const valid=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
const workouts=state.workouts.filter(w=>!Object.hasOwn(state.deleted?.workouts||{},w.id));
const exercises=new Map();for(const w of workouts)for(const e of w.entries||[])exercises.set(String(e.id),e);
for(const routine of state.routines||[])for(const e of routine.ex||[])if(!exercises.has(String(e.id)))exercises.set(String(e.id),e);
const custom=new Map((state.customEx||[]).map(e=>[String(e.id),e]));
const muscleMap={biceps:'BICEPS',triceps:'TRICEPS',delts:'SHOULDERS',pectorals:'CHEST',lats:'LATS','upper back':'BACK',abs:'ABDOMINALS',glutes:'GLUTES',hamstrings:'HAMSTRINGS',quads:'QUADRICEPS',calves:'CALVES',forearms:'FOREARMS'};
const equipMap={'body weight':'BODY_ONLY',dumbbell:'DUMBBELL',barbell:'BARBELL',cable:'CABLE','leverage machine':'MACHINE',band:'BANDS','smith machine':'SMITH_MACHINE','stationary bike':'SPIN_BIKE'};
const mapSet=(set,index)=>nativeSet(set,index,state.unit);
const now=new Date(),report={sourceWorkouts:state.workouts.length,importedWorkouts:0,importedExerciseEntries:0,importedSets:0,importedRoutines:0,retainedWeighIns:state.bodyweight?.length||0,unknownExerciseNames:0};
try{
 await prisma.user.count(); // Refuse import until native migrations have completed.
 await prisma.$executeRawUnsafe('CREATE TABLE IF NOT EXISTS aurora_import_snapshot(id text PRIMARY KEY,sha256 text NOT NULL,source jsonb NOT NULL,report jsonb NOT NULL,created_at timestamptz NOT NULL DEFAULT now())');
 const existing=await prisma.$queryRawUnsafe("SELECT sha256 FROM aurora_import_snapshot WHERE id='opengym'");
 if(existing.length){if(existing[0].sha256!==hash)throw Error('A different snapshot exists. Refusing to overwrite evaluation data.');console.log(JSON.stringify({alreadyImported:true,sha256:hash}));process.exit(0)}
 await prisma.$transaction(async db=>{
  await db.user.upsert({where:{id:userId},create:{id:userId,name:'Rafael',firstName:'Rafael',lastName:'',email:userEmail,emailVerified:true,locale:'pt',role:'admin',createdAt:now,updatedAt:now},update:{}});
  async function attribute(exerciseId,name,value){
   const a=await db.exerciseAttributeName.upsert({where:{name},create:{name},update:{}});
   const v=await db.exerciseAttributeValue.upsert({where:{attributeNameId_value:{attributeNameId:a.id,value}},create:{attributeNameId:a.id,value},update:{}});
   await db.exerciseAttribute.upsert({where:{exerciseId_attributeNameId_attributeValueId:{exerciseId,attributeNameId:a.id,attributeValueId:v.id}},create:{exerciseId,attributeNameId:a.id,attributeValueId:v.id},update:{}});
  }
  for(const [id,entry] of exercises){const c=custom.get(id),cat=catalogue[id];const name=c?.n||cat?.displayName||cat?.name;
   if(!name){report.unknownExerciseNames++;throw Error('Exercise name is missing in the original catalogue: '+id)}
   const exerciseId=stable('ex',id),description=[c?.desc||cat?.description||'',...(cat?.instructions||[])].filter(Boolean).join('\n');
   await db.exercise.upsert({where:{id:exerciseId},create:{id:exerciseId,name,nameEn:name,description,descriptionEn:description,slug:exerciseId,slugEn:exerciseId},update:{}});
   const cardio=entry.mode==='cardio'||(c&&/garmin-ex/.test(id));
   await attribute(exerciseId,'TYPE',cardio?'CARDIO':cat?.category==='calisthenics'?'CALISTHENIC':'STRENGTH');
   if(muscleMap[cat?.target])await attribute(exerciseId,'PRIMARY_MUSCLE',muscleMap[cat.target]);
   if(equipMap[cat?.equipment])await attribute(exerciseId,'EQUIPMENT',equipMap[cat.equipment]);
  }
  for(const w of workouts){if(!valid(w.start)||!valid(w.end)||w.end<w.start)throw Error('Workout timestamps require review: '+w.id);
   const comment=['Cópia do openGym/Garmin · '+(w.name||'Treino'), 'Data original: '+w.d,w.note||'',w.garminActivity?'Garmin: '+JSON.stringify(w.garminActivity):'',...(w.entries||[]).map(e=>e.note||'').filter(Boolean)].filter(Boolean).join('\n');
   const session=await db.workoutSession.create({data:{id:stable('workout',w.id),userId,startedAt:new Date(w.start),endedAt:new Date(w.end),duration:Math.round((w.end-w.start)/1000),ratingComment:comment,muscles:[]}});
   for(const [index,entry] of (w.entries||[]).entries()){
    const item=await db.workoutSessionExercise.create({data:{id:stable('entry',w.id+':'+index),workoutSessionId:session.id,exerciseId:stable('ex',entry.id),order:index}});
    for(const [i,set] of (entry.sets||[]).entries()){await db.workoutSet.create({data:{id:stable('set',w.id+':'+index+':'+i),workoutSessionExerciseId:item.id,...mapSet(set,i)}});report.importedSets++}
    report.importedExerciseEntries++;
   }report.importedWorkouts++;
  }
  const translated=(prefix,value)=>Object.fromEntries(['','En','Es','Pt','Ru','ZhCn'].map(s=>[prefix+s,value]));
  for(const routine of (state.routines||[]).filter(r=>!Object.hasOwn(state.deleted?.routines||{},r.id))){
   const id=stable('plan',routine.id),slug='opengym-'+id,name=routine.name||'Plano importado';
   const description='Plano copiado do openGym. O nível Iniciante é um campo técnico obrigatório do Workout Cool e não é uma avaliação do usuário. A programação original está preservada no snapshot.';
   await db.program.create({data:{id,...translated('slug',slug),...translated('title',name),...translated('description',description),category:'Importado do openGym',image:'/logo.png',level:'BEGINNER',type:(routine.ex||[]).every(e=>valid(e.min))?'CARDIO':'STRENGTH',durationWeeks:1,sessionsPerWeek:1,sessionDurationMin:Math.max(1,Math.round((routine.ex||[]).reduce((sum,e)=>sum+(e.min||0)*(e.sets||1),0))),isPremium:false,isActive:true,visibility:'PUBLISHED'}});
   const week=await db.programWeek.create({data:{programId:id,weekNumber:1,...translated('title',name),...translated('description','Rotina original importada.')}});
   const session=await db.programSession.create({data:{weekId:week.id,sessionNumber:1,estimatedMinutes:Math.max(1,Math.round((routine.ex||[]).reduce((sum,e)=>sum+(e.min||0)*(e.sets||1),0))),isPremium:false,...translated('title',name),...translated('slug',slug),...translated('description','Rotina original importada.')}});
   for(const [i,e] of (routine.ex||[]).entries()){
    const pe=await db.programSessionExercise.create({data:{sessionId:session.id,exerciseId:stable('ex',e.id),order:i,...translated('instructions','Valores copiados do plano original; detalhes completos preservados no snapshot.')}});
    for(let n=0;n<(e.sets||1);n++){const values=mapSet(e,n);const {type,completed,...set}=values;await db.programSuggestedSet.create({data:{programSessionExerciseId:pe.id,...set}})}
   }
   await db.userProgramEnrollment.create({data:{userId,programId:id}});report.importedRoutines++;
  }
  await db.$executeRawUnsafe('INSERT INTO aurora_import_snapshot(id,sha256,source,report) VALUES($1,$2,$3::jsonb,$4::jsonb)','opengym',hash,JSON.stringify(state),JSON.stringify(report));
 },{timeout:180000,maxWait:10000});
 console.log(JSON.stringify({sha256:hash,...report}));
}catch(error){fs.writeFileSync('/tmp/workoutcool-import-error.log',String(error?.stack||error),{mode:0o600});console.error('Importação abortada; diagnóstico privado registrado sem expor os dados.');process.exitCode=1;}finally{await prisma.$disconnect()}
