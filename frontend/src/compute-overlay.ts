import * as THREE from 'three';

// Authored activity, never pressure/sensitivity or the model's actual batch location.
// One extra draw call; shared geometry is owned by FlowScene.
export function computeOverlay(geometry:THREE.BufferGeometry) {
  geometry.computeBoundingBox();
  const box=geometry.boundingBox!;
  const material=new THREE.ShaderMaterial({transparent:true,depthWrite:false,side:THREE.DoubleSide,
    polygonOffset:true,polygonOffsetFactor:-2,polygonOffsetUnits:-2,
    uniforms:{clock:{value:0},phase:{value:0},measured:{value:0},minimum:{value:box.min.clone()},span:{value:box.getSize(new THREE.Vector3())}},
    vertexShader:`varying vec3 location; void main(){location=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.);}`,
    fragmentShader:`uniform float clock;uniform float phase;uniform float measured;uniform vec3 minimum;uniform vec3 span;varying vec3 location;
    void main(){vec3 q=(location-minimum)/max(span,vec3(.001));
      float scan=.5+.5*sin(clock*.95+phase);float band=exp(-pow((q.x-scan)/.14,2.));
      float patches=.55+.45*sin(q.y*18.+q.z*13.+clock*1.8)*sin(q.x*19.-q.z*9.);
      float intensity=clamp(band*patches,0.,1.);
      vec3 cool=vec3(.02,.35,.80);vec3 warm=mix(vec3(.03,.96,.78),vec3(1.,.48,.08),smoothstep(.3,.8,intensity));
      gl_FragColor=measured>.5?vec4(.4,1.,1.,band*.2):vec4(mix(cool,warm,smoothstep(.02,.55,intensity)),.22+.64*intensity);}`});
  const mesh=new THREE.Mesh(geometry,material);mesh.visible=false;mesh.renderOrder=4;
  return mesh;
}
