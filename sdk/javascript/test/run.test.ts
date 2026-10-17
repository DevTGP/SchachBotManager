// run in a real bot process: transports, protected stdout, options, data and exit codes.
import assert from "node:assert/strict";
import { mkdirSync, mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs";
import net from "node:net";
import { tmpdir } from "node:os";
import path from "node:path";
import { after, before, test } from "node:test";

import { Bot, run } from "../src/index.ts";
import type { BotClass } from "../src/index.ts";
import { answers, MESSAGES, runBot, writeBot } from "./bot-process.ts";

let root = "";
let count = 0;

before(() => {
  root = mkdtempSync(path.join(tmpdir(), "sbm-run-"));
});

after(() => {
  rmSync(root, { recursive: true, force: true });
});

/** A fresh directory below a fresh project directory for one bot. */
function directory(): string {
  count += 1;
  const bot = path.join(root, `project-${count}`, "bot");
  mkdirSync(bot, { recursive: true });
  return bot;
}

function types(stdout: string): unknown[] {
  return answers(stdout).map((message) => message.type);
}

test("stdout carries only the protocol", async () => {
  const start = 'console.log("from console"); process.stdout.write("raw write\\n");';
  const finished = await runBot(writeBot(directory(), { start }));
  assert.equal(finished.code, 0, finished.stderr);
  assert.deepEqual(types(finished.stdout), ["ready", "move"]);
  assert.match(finished.stderr, /from console/);
  assert.match(finished.stderr, /raw write/);
});

test("loadData next to the main file", async () => {
  const bot = directory();
  mkdirSync(path.join(bot, "data"));
  writeFileSync(path.join(bot, "data", "book.bin"), "opening");
  const start = 'sbm.Log.info(new TextDecoder().decode(sbm.loadData("book.bin")));';
  const finished = await runBot(writeBot(bot, { start }));
  assert.equal(finished.code, 0, finished.stderr);
  assert.match(finished.stderr, /INFO {2}opening/);
});

test("loadData from SBM_DATA_DIR", async () => {
  const bot = directory();
  const server = path.join(bot, "server");
  mkdirSync(server);
  writeFileSync(path.join(server, "book.bin"), "server");
  const start = 'sbm.Log.info(new TextDecoder().decode(sbm.loadData("book.bin")));';
  const finished = await runBot(writeBot(bot, { start }), [], undefined, { SBM_DATA_DIR: server });
  assert.match(finished.stderr, /INFO {2}server/);
});

test("an exception ends the process with code 1", async () => {
  const turn = 'throw new RangeError("lost");';
  const finished = await runBot(writeBot(directory(), { turn }));
  assert.equal(finished.code, 1);
  assert.deepEqual(types(finished.stdout), ["ready"]);
  assert.match(finished.stderr, /ERROR chooseMove threw RangeError: lost/);
  assert.match(finished.stderr, /my_bot\.mjs/);
});

test("an unusable answer ends the process with code 1", async () => {
  const turn = 'return "e2e4";';
  const finished = await runBot(writeBot(directory(), { turn }));
  assert.equal(finished.code, 1);
  assert.match(finished.stderr, /ERROR chooseMove returned string, not a Move/);
});

test("an exception in the constructor ends the process with code 1", async () => {
  const code = {
    run: 'class Broken extends TestBot { constructor() { super(); throw new Error("no"); } }\nawait sbm.run(Broken);',
  };
  const finished = await runBot(writeBot(directory(), code));
  assert.equal(finished.code, 1);
  assert.equal(finished.stdout, "");
  assert.match(finished.stderr, /ERROR new Broken\(\) threw Error: no/);
});

test("a protocol error ends the process with code 1", async () => {
  const finished = await runBot(writeBot(directory()), [], "not json\n");
  assert.equal(finished.code, 1);
  assert.match(finished.stderr, /ERROR protocol error/);
});

test("log level and file from arguments", async () => {
  const bot = directory();
  const logFile = path.join(bot, "bot.log");
  const turn = 'sbm.Log.debug("deep"); sbm.Log.trace("deeper");';
  const argv = ["--log-level", "debug", "--log-file", logFile];
  const finished = await runBot(writeBot(bot, { turn }), argv);
  assert.equal(finished.code, 0, finished.stderr);
  assert.match(finished.stderr, /\[ply 0\] DEBUG deep/);
  const written = readFileSync(logFile, "utf-8");
  assert.match(written, /\[ply 0\] DEBUG deep/);
  assert.doesNotMatch(written, /deeper/);
});

test("arguments win over the environment", async () => {
  const file = writeBot(directory(), { turn: 'sbm.Log.info("visible");' });
  const quiet = await runBot(file, [], undefined, { SBM_LOG_LEVEL: "warn" });
  assert.doesNotMatch(quiet.stderr, /visible/);
  const loud = await runBot(file, ["--log-level", "info"], undefined, { SBM_LOG_LEVEL: "warn" });
  assert.match(loud.stderr, /visible/);
});

test("unknown arguments are left to the bot", async () => {
  const start = "sbm.Log.info(JSON.stringify(process.argv.slice(2)));";
  const argv = ["--depth", "4", "--log-level", "info"];
  const finished = await runBot(writeBot(directory(), { start }), argv);
  assert.equal(finished.code, 0, finished.stderr);
  assert.match(finished.stderr, /INFO {2}\["--depth","4","--log-level","info"\]/);
});

const INVALID: [string[], Record<string, string>][] = [
  [["--log-level", "loud"], {}],
  [["--tcp", "70000"], {}],
  [[], { SBM_TRANSPORT: "pipe" }],
];

for (const [argv, variables] of INVALID) {
  test(`invalid options ${JSON.stringify(argv)} ${JSON.stringify(variables)}`, async () => {
    const finished = await runBot(writeBot(directory()), argv, undefined, variables);
    assert.equal(finished.code, 1);
    assert.equal(finished.stdout, "");
    assert.match(finished.stderr, /^sbm: /);
  });
}

test("remote games need the Python SDK for now", async () => {
  const argv = ["--remote", "https://example.org", "--opponent", "Material"];
  const finished = await runBot(writeBot(directory()), argv);
  assert.equal(finished.code, 1);
  assert.equal(finished.stdout, "");
  assert.match(finished.stderr, /ERROR this SDK cannot play remote games yet/);
});

test("the viewer is announced as missing, but not in the sandbox", async () => {
  const file = writeBot(directory(), { run: "await sbm.run(TestBot, { viewer: true });" });
  const local = await runBot(file);
  assert.equal(local.code, 0, local.stderr);
  assert.match(local.stderr, /WARN {2}this SDK has no viewer program yet/);
  const sandbox = await runBot(file, [], undefined, { SBM_NO_VIEWER: "1" });
  assert.equal(sandbox.code, 0, sandbox.stderr);
  assert.doesNotMatch(sandbox.stderr, /viewer/);
});

function freePort(): Promise<number> {
  return new Promise((resolve, reject) => {
    const probe = net.createServer();
    probe.once("error", reject);
    probe.listen(0, "127.0.0.1", () => {
      const port = (probe.address() as net.AddressInfo).port;
      probe.close(() => resolve(port));
    });
  });
}

test("an unreachable arena", async () => {
  const port = await freePort();
  const finished = await runBot(writeBot(directory()), ["--tcp", String(port)]);
  assert.equal(finished.code, 1);
  assert.match(
    finished.stderr,
    new RegExp(`ERROR cannot connect to the arena on 127\\.0\\.0\\.1:${port}`),
  );
});

/** A referee on a TCP port that plays MESSAGES and collects the answers. */
function tcpReferee(): Promise<{ port: number; received: Promise<unknown[]> }> {
  return new Promise((resolve, reject) => {
    let done: (types: unknown[]) => void = () => undefined;
    const received = new Promise<unknown[]>((resolveReceived) => {
      done = resolveReceived;
    });
    const server = net.createServer((socket) => {
      const types: unknown[] = [];
      let buffer = "";
      let next = 0;
      const sendNext = (): void => {
        const message = MESSAGES[next];
        next += 1;
        socket.write(`${JSON.stringify(message)}\n`);
        if (message.type === "game_over") {
          socket.end();
          server.close();
          done(types);
        }
      };
      socket.setEncoding("utf-8");
      socket.on("data", (chunk: string) => {
        buffer += chunk;
        for (let end = buffer.indexOf("\n"); end >= 0; end = buffer.indexOf("\n")) {
          types.push((JSON.parse(buffer.slice(0, end)) as { type: unknown }).type);
          buffer = buffer.slice(end + 1);
          sendNext();
        }
      });
      sendNext();
    });
    server.once("error", reject);
    server.listen(0, "127.0.0.1", () => {
      resolve({ port: (server.address() as net.AddressInfo).port, received });
    });
  });
}

for (const fromEnvironment of [false, true]) {
  test(`tcp${fromEnvironment ? " from the environment" : ""}`, async () => {
    const referee = await tcpReferee();
    const file = writeBot(directory(), { start: 'console.log("still stdout");' });
    const finished = fromEnvironment
      ? await runBot(file, [], "", { SBM_TRANSPORT: "tcp", SBM_PORT: String(referee.port) })
      : await runBot(file, ["--tcp", String(referee.port)], "");
    assert.equal(finished.code, 0, finished.stderr);
    assert.deepEqual(await referee.received, ["ready", "move"]);
    assert.equal(finished.stdout, "still stdout\n");
  });
}

test("run needs a class that extends Bot", async () => {
  await assert.rejects(run(Object as unknown as BotClass), /class that extends Bot/);
  await assert.rejects(run((() => undefined) as unknown as BotClass), /class that extends Bot/);
  abstract class NoMove extends Bot {}
  await assert.rejects(run(NoMove as unknown as BotClass), /has no method chooseMove/);
  class Fine extends Bot {
    chooseMove(): never {
      throw new Error("unused");
    }
  }
  await assert.rejects(run(Fine, { viewer: "yes" as unknown as boolean }), /viewer must be/);
});
