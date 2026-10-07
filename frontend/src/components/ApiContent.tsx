import type { ReactNode } from "react";

import type { ApiState } from "../hooks/useApi";
import { ErrorMessage } from "./ErrorMessage";
import { Loading } from "./Loading";

/** Shows the data once it is there; an error only while no data is shown. */
export function ApiContent<T>({
  state,
  children,
}: {
  state: ApiState<T>;
  children: (data: T) => ReactNode;
}) {
  if (state.data !== undefined) return children(state.data);
  if (state.error) return <ErrorMessage error={state.error} />;
  return <Loading />;
}
