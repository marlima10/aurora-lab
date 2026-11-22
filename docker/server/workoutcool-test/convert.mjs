const valid=v=>typeof v==='number'&&Number.isFinite(v)&&v>=0;
export function nativeSet(set,index,unit){const types=[],valuesInt=[],valuesSec=[],units=[];const add=(type,integer=0,seconds=0)=>{types.push(type);valuesInt.push(integer);valuesSec.push(seconds);units.push(unit==='lbs'?'lbs':'kg')};
 if(valid(set.min))add('TIME',0,Math.round(set.min*60));
 if(valid(set.w)){if(!Number.isInteger(set.w))throw Error('Fractional weight needs explicit migration; refusing to round.');add('WEIGHT',set.w)}
 if(valid(set.r)){if(!Number.isInteger(set.r))throw Error('Invalid repetitions.');add('REPS',set.r)}
 return {setIndex:index,type:types[0]||'NA',types,valuesInt,valuesSec,units,completed:set.done===true};
}