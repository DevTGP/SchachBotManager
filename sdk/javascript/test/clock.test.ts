// Clock: times from turn and elapsed time of the turn.
import assert from "node:assert/strict";
import { test } from "node:test";

import { Clock } from "../src/index.ts";

test("times as given", () => {
  const clock = new Clock(1000, 2000, 30);
  assert.equal(clock.remainingMs(), 1000);
  assert.equal(clock.opponentRemainingMs(), 2000);
  assert.equal(clock.incrementMs(), 30);
  assert.equal(String(clock), "Clock(remainingMs=1000, opponentRemainingMs=2000, incrementMs=30)");
});

test("elapsed time grows in whole milliseconds", async () => {
  const clock = new Clock(1000, 1000, 0);
  const first = clock.elapsedMs();
  assert.ok(Number.isInteger(first) && first >= 0);
  await new Promise((resolve) => setTimeout(resolve, 30));
  const second = clock.elapsedMs();
  assert.ok(Number.isInteger(second) && second >= first + 20, `elapsed ${second}`);
  assert.equal(clock.remainingMs(), 1000);
});
