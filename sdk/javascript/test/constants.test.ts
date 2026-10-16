// The constants of spec/api/constants.json as named exports (E204).
import assert from "node:assert/strict";
import { test } from "node:test";

import * as sbm from "../src/index.ts";
import { constants } from "./spec.ts";

const exports = sbm as unknown as Record<string, unknown>;

for (const constant of constants()) {
  test(constant.name, () => {
    const value = exports[constant.name];
    if (constant.type === "Move") {
      assert.ok(value instanceof sbm.Move);
      assert.equal(value.value(), constant.value);
      assert.equal(value, (sbm.Move as unknown as Record<string, unknown>)[constant.name]);
    } else {
      assert.equal(value, constant.value);
    }
  });
}
