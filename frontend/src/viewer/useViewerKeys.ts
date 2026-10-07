import { useEffect } from "react";

/** Arrow keys step, Home and End jump, Space plays; form fields keep their keys. */
export function useViewerKeys(
  ply: number,
  total: number,
  goTo: (ply: number) => void,
  toggle: () => void,
) {
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.altKey || event.ctrlKey || event.metaKey) return;
      const target = event.target instanceof Element ? event.target : null;
      if (target?.closest("input, select, textarea")) return;
      switch (event.key) {
        case "ArrowLeft":
          goTo(ply - 1);
          break;
        case "ArrowRight":
          goTo(ply + 1);
          break;
        case "Home":
          goTo(0);
          break;
        case "End":
          goTo(total);
          break;
        case " ":
          // A focused button already reacts to Space with a click.
          if (target?.closest("button")) return;
          toggle();
          break;
        default:
          return;
      }
      event.preventDefault();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [ply, total, goTo, toggle]);
}
