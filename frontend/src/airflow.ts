export interface FlowPath {positions:number[];speedMps:number[];timeSeconds:number[]}
export interface Airflow {schemaVersion:'zephyr.airflow.v1';geometryId:string;meshHash:string;source:'nvidia-volume';model:string;checkpointSha256:string;units:'m/s';streamVelocityMps:number;gridShape:number[];paths:FlowPath[];seconds:number;speedRangeMps:number[];playbackTimeScale:number;createdAt?:string}
export function validateAirflow(value:Airflow,geometryId:string,meshHash?:string):Airflow {
 if(value?.schemaVersion!=='zephyr.airflow.v1'||value.geometryId!==geometryId||value.source!=='nvidia-volume'||value.units!=='m/s'||!/^([a-f0-9]{64})$/.test(value.meshHash)||!/^([a-f0-9]{64})$/.test(value.checkpointSha256)||(meshHash&&value.meshHash!==meshHash)||!Number.isFinite(value.playbackTimeScale)||value.playbackTimeScale<=0||value.playbackTimeScale>1||!Number.isFinite(value.streamVelocityMps)||value.streamVelocityMps<=0||!Array.isArray(value.paths)||value.paths.length<1||value.paths.length>160)throw new Error('Airflow does not match this car or model');
 for(const p of value.paths){const n=p?.positions?.length/3;if(!Number.isInteger(n)||n<2||n>500||p.speedMps?.length!==n||p.timeSeconds?.length!==n||p.positions.some(v=>!Number.isFinite(v))||p.speedMps.some(v=>!Number.isFinite(v)||v<0)||p.timeSeconds.some((v,i)=>!Number.isFinite(v)||v<0||(i>0&&v<=p.timeSeconds[i-1])))throw new Error('Invalid predicted airflow path');}
 return value;
}
export function sampleFlowPath(path:FlowPath,time:number):[number,number,number]{
 const times=path.timeSeconds,duration=times[times.length-1],t=((time%duration)+duration)%duration;
 let lo=0,hi=times.length-1;while(hi-lo>1){const mid=(lo+hi)>>1;if(times[mid]<=t)lo=mid;else hi=mid;}
 const a=(t-times[lo])/(times[hi]-times[lo]);return [0,1,2].map(k=>path.positions[lo*3+k]*(1-a)+path.positions[hi*3+k]*a) as [number,number,number];
}
