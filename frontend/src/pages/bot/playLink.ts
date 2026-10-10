/**
 * Where "Play" leads for another version: the owner's own form, else the admin form; null
 * if the viewer may not set games between the two (E160).
 */
export function playLink(
  current: string,
  other: string,
  viewer: { isOwner: boolean; isAdmin: boolean },
): string | null {
  if (viewer.isOwner) return `/account/bots?own=${current}&opponent=${other}`;
  if (viewer.isAdmin) return `/admin?white=${current}&black=${other}`;
  return null;
}
