// Keep static/hidden views off the GPU; motion has a bounded presentation rate.
export function framePolicy(s:{visible:boolean;hidden:boolean;dirty:boolean;moving:boolean;busy:boolean;now:number;last:number}) {
  if (!s.visible || s.hidden) return {draw:false,again:false};
  const due=s.now-s.last>=1000/(s.busy?20:30)-.1;
  return {draw:s.dirty || (s.moving&&due),again:s.moving};
}
export function computationActive(state:string) {return state==='running';}
export function activityCaption(stage:string,percent:number|null,hasFields:boolean) {
  return `${stage.replaceAll('-',' ')}${percent===null?'':` · ${percent}% of calculation`} · ${hasFields?'Recorded baseline field + illustrative activity sweep':'Illustrative activity scan · not a pressure result'}`;
}
