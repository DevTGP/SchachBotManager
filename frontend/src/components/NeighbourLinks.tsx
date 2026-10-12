import { Link } from "react-router";

/** One season or edition of a competition. */
interface Numbered {
  id: string;
  number: number;
}

/**
 * Links to the season or edition before and after `number` among `entries` (E188); nothing when
 * there is neither.
 */
export function NeighbourLinks({
  entries,
  number,
  path,
  previous,
  next,
}: {
  entries: Numbered[];
  number: number;
  path: string;
  previous: (number: number) => string;
  next: (number: number) => string;
}) {
  const before = entries.find((entry) => entry.number === number - 1);
  const after = entries.find((entry) => entry.number === number + 1);
  if (!before && !after) return null;
  return (
    <nav className="neighbour-links">
      {before && <Link to={`${path}/${before.id}`}>{previous(before.number)}</Link>}
      {after && <Link to={`${path}/${after.id}`}>{next(after.number)}</Link>}
    </nav>
  );
}
