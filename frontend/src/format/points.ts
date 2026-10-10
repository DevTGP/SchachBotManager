/** Points of a series as 6½, ½ or 3; a win is 1, a draw ½ (E155). */
export function formatPoints(points: number): string {
  const whole = Math.floor(points);
  const half = points - whole >= 0.5;
  if (!half) return String(whole);
  return whole === 0 ? "½" : `${whole}½`;
}
