import type { ReactNode } from "react";

/**
 * A table that scrolls sideways on small screens with a shadow at the hidden edge, or the empty
 * text without rows. Columns marked optional disappear on phones (E168).
 */
export function TableShell({
  rows,
  empty,
  className,
  children,
}: {
  rows: number;
  empty: ReactNode;
  className?: string;
  children: ReactNode;
}) {
  if (rows === 0) return <p className="muted">{empty}</p>;
  return (
    <div className="table-scroll">
      <table className={className}>{children}</table>
    </div>
  );
}
