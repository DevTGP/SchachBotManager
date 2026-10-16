// Start options from the command line and the environment (E61).
import assert from "node:assert/strict";
import { test } from "node:test";

import { DEBUG, ERROR, INFO, OFF } from "../src/index.ts";
import { DEFAULT_PORT, OptionsError, parseOptions } from "../src/options.ts";

const DEFAULTS = { transport: "stdio", port: DEFAULT_PORT, logLevel: INFO, logFile: undefined };

test("defaults", () => {
  assert.deepEqual(parseOptions([], {}), DEFAULTS);
});

test("environment", () => {
  const environment = {
    SBM_TRANSPORT: "TCP",
    SBM_PORT: "9000",
    SBM_LOG_LEVEL: "debug",
    SBM_LOG_FILE: "bot.log",
  };
  assert.deepEqual(parseOptions([], environment), {
    transport: "tcp",
    port: 9000,
    logLevel: DEBUG,
    logFile: "bot.log",
  });
  assert.deepEqual(parseOptions([], { SBM_LOG_FILE: "" }), DEFAULTS);
});

test("arguments win over the environment", () => {
  const environment = { SBM_PORT: "9000", SBM_LOG_LEVEL: "debug", SBM_LOG_FILE: "env.log" };
  const argv = ["--tcp", "7000", "--log-level=Off", "--log-file", "arg.log"];
  assert.deepEqual(parseOptions(argv, environment), {
    transport: "tcp",
    port: 7000,
    logLevel: OFF,
    logFile: "arg.log",
  });
  assert.equal(parseOptions(["--log-file="], environment).logFile, undefined);
});

test("--tcp without a port", () => {
  assert.deepEqual(parseOptions(["--tcp"], {}), { ...DEFAULTS, transport: "tcp" });
  assert.equal(parseOptions(["--tcp"], { SBM_PORT: "9000" }).port, 9000);
  assert.equal(parseOptions(["--tcp", "--log-level", "warn"], {}).port, DEFAULT_PORT);
  assert.equal(parseOptions(["--tcp=7001"], {}).port, 7001);
});

test("other arguments belong to the bot", () => {
  const argv = ["--depth", "4", "book.bin", "--log-level", "error", "-v"];
  assert.deepEqual(parseOptions(argv, {}), { ...DEFAULTS, logLevel: ERROR });
  assert.deepEqual(parseOptions(["--", "--tcp", "--log-level", "loud"], {}), DEFAULTS);
});

test("--remote selects the remote transport", () => {
  const argv = ["--remote", "https://example.org", "--opponent", "Material"];
  assert.equal(parseOptions(argv, {}).transport, "remote");
  assert.equal(parseOptions([], { SBM_TRANSPORT: "remote" }).transport, "remote");
});

const INVALID: [string[], Record<string, string>][] = [
  [["--tcp", "0"], {}],
  [["--tcp", "65536"], {}],
  [["--tcp", "port"], {}],
  [["--tcp", "-1"], {}],
  [["--log-level", "loud"], {}],
  [["--log-level"], {}],
  [["--log-level", "--tcp"], {}],
  [["--remote"], {}],
  [[], { SBM_TRANSPORT: "pipe" }],
  [[], { SBM_PORT: "-1" }],
  [[], { SBM_PORT: "1e3" }],
  [[], { SBM_LOG_LEVEL: "5" }],
];

for (const [argv, environment] of INVALID) {
  test(`invalid: ${JSON.stringify(argv)} ${JSON.stringify(environment)}`, () => {
    assert.throws(() => parseOptions(argv, environment), OptionsError);
  });
}
