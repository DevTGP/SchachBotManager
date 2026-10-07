import { useCallback } from "react";
import { useSearchParams } from "react-router";

export interface ViewerPly {
  /** Moves played in the shown position; 0 is the start position. */
  ply: number;
  /** A running match without a chosen move shows each new move as it arrives. */
  following: boolean;
  goTo: (ply: number) => void;
  follow: () => void;
}

/**
 * The shown move lives in the URL (?ply=N), so a link leads to the same position. Without it the
 * viewer shows the last move; for a running match that means following it live.
 */
export function useViewerPly(total: number, live: boolean): ViewerPly {
  const [params, setParams] = useSearchParams();
  const chosen = parsePly(params.get("ply"));
  const ply = chosen === undefined ? total : Math.min(chosen, total);

  const goTo = useCallback(
    (target: number) => {
      const clamped = Math.max(0, Math.min(target, total));
      setParams(
        (previous) => {
          const next = new URLSearchParams(previous);
          // Stepping onto the last move of a running match goes back to following it.
          if (live && clamped === total) next.delete("ply");
          else next.set("ply", String(clamped));
          return next;
        },
        { replace: true },
      );
    },
    [total, live, setParams],
  );

  const follow = useCallback(() => {
    setParams(
      (previous) => {
        const next = new URLSearchParams(previous);
        next.delete("ply");
        return next;
      },
      { replace: true },
    );
  }, [setParams]);

  return { ply, following: live && chosen === undefined, goTo, follow };
}

function parsePly(value: string | null): number | undefined {
  if (value === null || !/^\d+$/.test(value)) return undefined;
  return Number(value);
}
