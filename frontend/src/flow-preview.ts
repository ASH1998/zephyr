/** Authored wake comparison for the demo only; never inferred from surface fields. */
export function previewWake(x: number, y: number, z: number, phase: number, candidate: number): [number, number, number] {
  const t = Math.max(0, Math.min(1, (x - 2.15) / 2.5));
  const wake = t * t * (3 - 2 * t), baseline = 1 - candidate;
  return [x, y + Math.sin(x * 4.2 + phase * 6.28) * .22 * wake * baseline,
    z * (1 - .17 * wake * candidate) + Math.sin(x * 3.8 + phase * 6.28) * .38 * wake * baseline];
}
