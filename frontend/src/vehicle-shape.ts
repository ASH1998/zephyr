import { MathUtils } from 'three';

/** Baseline styling only, before the protected mask and candidate are created. */
export function cabinLift(x: number, y: number): number {
  // The source roof is 1.26 m after normalization. Match its actual greenhouse.
  const cabin = MathUtils.smoothstep(x, -1.5, -.4) * (1 - MathUtils.smoothstep(x, .85, 1.85));
  return .28 * cabin * MathUtils.smoothstep(y, .98, 1.24);
}
