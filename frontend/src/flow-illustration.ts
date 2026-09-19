// A geometry-following explanation, deliberately separate from predicted velocity.
export interface IllustrationPath { positions: number[]; wake: boolean; vortexSide?: -1 | 1 }
export function illustrateFlow(positions: ArrayLike<number>, aircraft = false): IllustrationPath[] {
  const lo=[Infinity,Infinity,Infinity], hi=[-Infinity,-Infinity,-Infinity];
  for(let i=0;i<positions.length;i++) {const k=i%3;lo[k]=Math.min(lo[k],positions[i]);hi[k]=Math.max(hi[k],positions[i]);}
  const length=hi[0]-lo[0], width=hi[2]-lo[2], height=hi[1]-lo[1];
  const margin=Math.max(.07,length*.018), approach=length*.42, exit=length*.55;
  const bins=64, step=length/(bins-1), result:IllustrationPath[]=[];
  const smooth=(v:number)=>{const t=Math.max(0,Math.min(1,v));return t*t*(3-2*t);};
  // An upper envelope spreads the turn upstream, while keeping clearance from
  // every sampled section. No physics or speed is inferred from these curves.
  function envelope(values:number[], base:number, spread:number) {
    return (x:number)=>{let v=base;for(let b=0;b<bins;b++){
      const distance=Math.max(0,Math.abs(x-(lo[0]+b*step))-step);
      v=Math.max(v,base+(values[b]-base)*Math.exp(-Math.pow(distance/spread,2)));
    }return v;};
  }
  const lanes=aircraft?11:5;
  for(let layer=0;layer<2;layer++) for(let lane=0;lane<lanes;lane++) {
    const z=(lo[2]+hi[2])/2+(lane/(lanes-1)-.5)*width*(aircraft?.92:.72);
    const base=lo[1]+height*(aircraft?.28:.42), values=Array(bins).fill(base);
    for(let i=0;i<positions.length;i+=3) if(Math.abs(positions[i+2]-z)<width/(lanes-1)*.75+margin){
      const b=Math.min(bins-1,Math.floor((positions[i]-lo[0])/step));values[b]=Math.max(values[b],positions[i+1]+margin);
    }
    const roof=envelope(values,base,length*(aircraft?.1:.16)), points:number[]=[];
    for(let j=0;j<=160;j++) {const x=lo[0]-approach+j/160*(length+approach+exit),wake=smooth((x-hi[0])/exit);
      const y=roof(x)+layer*margin*2.5+Math.sin(wake*Math.PI*3+lane*.5)*wake*height*.09;
      points.push(x,y,z+Math.sin(wake*Math.PI*2+lane*.65)*wake*width*.07);
    }
    result.push({positions:points,wake:false});
  }
  if(!aircraft) for(const sign of [-1,1]) for(let band=0;band<3;band++) for(let lane=0;lane<4;lane++) {
    const y=lo[1]+height*(.22+lane*.16), center=(lo[2]+hi[2])/2, base=width*.26;
    const values=Array(bins).fill(base);
    for(let i=0;i<positions.length;i+=3) if(Math.abs(positions[i+1]-y)<height*.18) {
      const b=Math.min(bins-1,Math.floor((positions[i]-lo[0])/step));values[b]=Math.max(values[b],sign*(positions[i+2]-center)+margin);
    }
    const side=envelope(values,base,length*.17), points:number[]=[];
    const outward=width*band*.27;
    for(let j=0;j<=160;j++) {const x=lo[0]-approach+j/160*(length+approach+exit),wake=smooth((x-hi[0])/exit);
      points.push(x,y+Math.sin(wake*Math.PI*3+lane*.65)*wake*height*.08,center+sign*(side(x)+margin*.6+outward)+Math.sin(wake*Math.PI*3+lane*.7)*wake*width*.09);
    }
    result.push({positions:points,wake:false});
  }
  if(aircraft) {
    const center=(lo[2]+hi[2])/2;
    // Two counter-rotating wake tubes originate at the outboard trailing edge,
    // not the tail. Several phased filaments make each spiral easy to follow.
    for(const sign of [-1,1] as const) {
      let trailing=-Infinity,tipY=0,count=0;
      for(let i=0;i<positions.length;i+=3)if(sign*(positions[i+2]-center)>width*.44)trailing=Math.max(trailing,positions[i]);
      for(let i=0;i<positions.length;i+=3)if(sign*(positions[i+2]-center)>width*.44&&positions[i]>trailing-length*.09){tipY+=positions[i+1];count++;}
      tipY=count?tipY/count:lo[1]+height*.4;
      const tipZ=center+sign*width*.47, end=hi[0]+length*.85;
      for(let strand=0;strand<3;strand++) {
        const points:number[]=[], phase=strand*Math.PI*2/3;
        for(let j=0;j<=240;j++) {
          const t=j/240,x=trailing+margin+t*(end-trailing-margin);
          const radius=width*.065*smooth(t/.2)*(1-.25*smooth((t-.7)/.3));
          const angle=sign*(t*Math.PI*7+phase);
          const sink=width*.028*t;
          points.push(x,tipY-sink+radius*Math.sin(angle),tipZ+radius*Math.cos(angle));
        }
        result.push({positions:points,wake:true,vortexSide:sign});
      }
    }
    return result;
  }
  // Detached curls explain the wake; they are not a claim of measured vortices.
  for(const sign of [-1,1]) for(let lane=0;lane<2;lane++) {
    const points:number[]=[];
    for(let j=0;j<=120;j++) {const t=j/120, radius=width*(aircraft?.055:.085)*Math.sin(Math.PI*t);
      points.push(hi[0]+margin+t*exit,lo[1]+height*(.4+lane*.18)+radius*Math.sin(t*Math.PI*5),sign*width*.27+sign*radius*Math.cos(t*Math.PI*5));
    }
    result.push({positions:points,wake:true});
  }
  return result;
}
