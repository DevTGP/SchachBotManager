import { useEffect, useRef } from "react";
import { useLocation } from "react-router";

/**
 * Whether the URL's fragment names `id`; the element behind the returned ref then scrolls into
 * view once it is there, as the content of a page arrives after the browser looked for it (E188).
 */
export function useHashTarget<T extends HTMLElement>(id: string) {
  const { hash } = useLocation();
  const ref = useRef<T>(null);
  const targeted = hash === `#${id}`;
  useEffect(() => {
    if (targeted) ref.current?.scrollIntoView?.({ block: "start" });
  }, [targeted]);
  return { ref, targeted };
}
