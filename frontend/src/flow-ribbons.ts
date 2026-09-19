import * as THREE from 'three';
import type {FlowPath} from './airflow';
import type {IllustrationPath} from './flow-illustration';

// Linear interpolation retains solver path segments: a spline can cut corners
// through the vehicle, and its arc length does not preserve travel time.
export class TraceCurve extends THREE.Curve<THREE.Vector3> {
  private values:number[];
  constructor(values:number[]) {super();this.values=values;}
  getPointAt(t:number,target=new THREE.Vector3()){return this.getPoint(t,target);}
  getTangentAt(t:number,target=new THREE.Vector3()){return this.getTangent(t,target);}
  getPoint(t:number,target=new THREE.Vector3()) {const n=this.values.length/3-1,s=Math.min(n,t*n),a=Math.min(n-1,Math.floor(s)),f=s-a;return target.set(...[0,1,2].map(k=>this.values[a*3+k]*(1-f)+this.values[(a+1)*3+k]*f) as [number,number,number]);}
}
export class FlowRibbons extends THREE.Group {
  private shaders:THREE.ShaderMaterial[]=[];
  private predicted:boolean;
  constructor(paths:(FlowPath|IllustrationPath)[],predicted:boolean,rear:number,scale=1) {
    super();this.predicted=predicted;
    paths.forEach((path,index)=>{
      const n=path.positions.length/3-1,curve=new TraceCurve(path.positions);
      const geometry=new THREE.TubeGeometry(curve,n,('vortexSide' in path?.018:.010)*scale,5,false);
      const colors=new Float32Array((n+1)*6*3), travel=new Float32Array((n+1)*6);
      const measured='timeSeconds' in path;
      const duration=measured?path.timeSeconds[n]:7;
      const color=new THREE.Color();
      for(let i=0;i<=n;i++) {
        if(measured)color.setHSL(.62-Math.min(1,path.speedMps[i]/60)*.57,.82,.61);
        else color.set('wake' in path&&path.wake?0xffb367:0x63dfe9).lerp(new THREE.Color(0xffb367),THREE.MathUtils.smoothstep(path.positions[i*3],rear,rear+scale)*.8);
        for(let j=0;j<6;j++){color.toArray(colors,(i*6+j)*3);travel[i*6+j]=measured?path.timeSeconds[i]:i/n*duration;}
      }
      geometry.setAttribute('color',new THREE.BufferAttribute(colors,3));geometry.setAttribute('travel',new THREE.BufferAttribute(travel,1));
      const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,depthTest:true,vertexColors:true,blending:THREE.AdditiveBlending,
        uniforms:{clock:{value:0},period:{value:measured?Math.max(.02,duration/3):2.2},phase:{value:measured?0:index*.17}},
        vertexShader:`attribute float travel; varying float t; varying float along; varying vec3 tint; void main(){t=travel;along=uv.x;tint=color;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
        fragmentShader:`uniform float clock;uniform float period;uniform float phase;varying float t;varying float along;varying vec3 tint;
        void main(){float behind=fract((clock-t)/period+phase);float trail=(1.-smoothstep(0.,.29,behind));float head=1.-smoothstep(0.,.04,behind);float fade=smoothstep(0.,.055,along)*(1.-smoothstep(.9,1.,along));gl_FragColor=vec4(mix(tint,vec3(.94,1.,1.),head*.8),(.075+trail*.85)*fade);}`});
      this.shaders.push(material);this.add(new THREE.Mesh(geometry,material));
    });
  }
  tick(seconds:number,playbackScale=1){for(const shader of this.shaders)shader.uniforms.clock.value=seconds*(this.predicted?playbackScale:1);}
  dispose(){this.traverse(o=>{if(o instanceof THREE.Mesh){o.geometry.dispose();(o.material as THREE.Material).dispose();}});this.clear();}
}
