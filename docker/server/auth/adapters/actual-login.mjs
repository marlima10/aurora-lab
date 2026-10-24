import {createHash} from 'node:crypto';
import fs from 'node:fs';
import {pathToFileURL} from 'node:url';
export const REVIEWED_SHA256='9301191f73c12b47b8d7af6c83b05e8732072dc98f06694cdcfe1dceede26778';
export const ORIGINAL='availableLoginMethods.length === 1 ? availableLoginMethods[0].method : getLoginMethod()';
export const REPLACEMENT='getLoginMethod() === "header" ? "header" : ('+ORIGINAL+')';
export function patchActual(source, expected=REVIEWED_SHA256){
  if(createHash('sha256').update(source).digest('hex')!==expected)throw Error('Actual source differs from reviewed revision');
  const text=source.toString('utf8');
  if(text.split('loginMethod: '+ORIGINAL).length!==2)throw Error('Unexpected Actual login discovery contract');
  const advertised='getLoginMethod() === "header" ? [{method:"header",active:1,displayName:"AuroraLAB"}] : listLoginMethods()';
  const declarations=['const availableLoginMethods = listLoginMethods();','const methods = listLoginMethods();'];
  for(const declaration of declarations){
    if(text.split(declaration).length!==2)throw Error('Unexpected Actual method-list contract');
  }
  return text.replace('loginMethod: '+ORIGINAL,'loginMethod: '+REPLACEMENT)
    .replace(declarations[0],'const availableLoginMethods = '+advertised+';')
    .replace(declarations[1],'const methods = '+advertised+';');
}
if(process.argv[1]&&import.meta.url===pathToFileURL(process.argv[1]).href){
  const path=process.argv[2];fs.writeFileSync(path,patchActual(fs.readFileSync(path)));
}
