// Walks an ESTree tree from acorn without recursion, so deep nesting cannot overflow the stack.
import type { AnyNode } from "acorn";

export interface Visit {
  readonly node: AnyNode;
  readonly parent: AnyNode | null;
  /** The property of parent that holds node. */
  readonly key: string | null;
}

const NOT_CHILDREN = new Set(["type", "loc", "start", "end", "range"]);

function isNode(value: unknown): value is AnyNode {
  return (
    typeof value === "object" &&
    value !== null &&
    typeof (value as { type?: unknown }).type === "string"
  );
}

/** Every node with its parent, in source order. */
export function* walk(root: AnyNode): Generator<Visit> {
  const stack: Visit[] = [{ node: root, parent: null, key: null }];
  for (let visit = stack.pop(); visit !== undefined; visit = stack.pop()) {
    yield visit;
    const children: Visit[] = [];
    for (const [key, value] of Object.entries(visit.node)) {
      if (NOT_CHILDREN.has(key)) {
        continue;
      }
      for (const item of Array.isArray(value) ? value : [value]) {
        if (isNode(item)) {
          children.push({ node: item, parent: visit.node, key });
        }
      }
    }
    stack.push(...children.reverse());
  }
}
