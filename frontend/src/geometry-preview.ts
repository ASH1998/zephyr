import type { Surface } from './data';
export interface GeometryPreview {schemaVersion:'zephyr.geometry-preview.v1';geometryId:string;meshHash?:string;displayColor?:number[];units:'m';positions:number[];triangles:number[];protectedMask:number[]}
export function previewSurface(value:GeometryPreview,geometryId='drivaer-1'):Surface {
  const n=value?.positions?.length/3;
  if(value?.schemaVersion!=='zephyr.geometry-preview.v1'||value.geometryId!==geometryId||value.units!=='m'||!Number.isInteger(n)||n<3||n>120000||!value.positions.every(Number.isFinite)||!Array.isArray(value.triangles)||!value.triangles.length||value.triangles.length%3||value.triangles.some(i=>!Number.isInteger(i)||i<0||i>=n)||value.protectedMask?.length!==n||value.protectedMask.some(v=>v!==0&&v!==1))throw new Error('Invalid geometry preview');
  if(value.displayColor&&(value.displayColor.length!==n*3||value.displayColor.some(c=>!Number.isFinite(c)||c<0||c>1)))throw new Error('Invalid car colors');
  // Rendering buffers only: field modes and export remain disabled until real inference.
  return {...value,pressurePa:Array(n).fill(0),normalSensitivity:Array(n).fill(0),wallShearPa:Array(n*3).fill(0),sensitivity:Array(n*3).fill(0),displacementM:Array(n).fill(0)};
}
