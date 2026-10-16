// Line channel: NDJSON framing, line limit and malformed input.
import assert from "node:assert/strict";
import { PassThrough } from "node:stream";
import { test } from "node:test";

import { Channel, MAX_LINE_BYTES, ProtocolError } from "../src/channel.ts";

function channel(input: PassThrough): { channel: Channel; written: string[] } {
  const written: string[] = [];
  const write = (line: string): Promise<void> => {
    written.push(line);
    return Promise.resolve();
  };
  return { channel: new Channel(input, write, () => input.destroy()), written };
}

function fed(...chunks: (string | Buffer)[]): Channel {
  const input = new PassThrough();
  for (const chunk of chunks) {
    input.write(chunk);
  }
  input.end();
  return channel(input).channel;
}

test("receives lines until the end", async () => {
  const reader = fed('{"type":"a"}\n{"type":"b","x":[1]}\r\n{"type":"c"}');
  assert.deepEqual(await reader.receive(), { type: "a" });
  assert.deepEqual(await reader.receive(), { type: "b", x: [1] });
  assert.deepEqual(await reader.receive(), { type: "c" });
  assert.equal(await reader.receive(), null);
  assert.equal(await reader.receive(), null);
});

test("lines may arrive in pieces and characters split across chunks", async () => {
  const bytes = Buffer.from('{"text":"Läufer ♗"}\n');
  const reader = fed(...Array.from(bytes, (byte) => Buffer.from([byte])));
  assert.deepEqual(await reader.receive(), { text: "Läufer ♗" });
  assert.equal(await reader.receive(), null);
});

test("waits for lines that arrive later", async () => {
  const input = new PassThrough();
  const { channel: reader } = channel(input);
  const pending = reader.receive();
  setTimeout(() => input.write('{"type":"late"}\n'), 5);
  assert.deepEqual(await pending, { type: "late" });
  input.end();
  assert.equal(await reader.receive(), null);
});

test("line limit", async () => {
  const text = "x".repeat(MAX_LINE_BYTES - '{"t":""}'.length);
  const longest = JSON.stringify({ t: text });
  assert.equal(Buffer.byteLength(longest), MAX_LINE_BYTES);
  const reader = fed(`${longest}\r\n${longest.slice(0, -1)}x"}\n`);
  assert.deepEqual(await reader.receive(), { t: text });
  await assert.rejects(reader.receive(), /longer/);
});

test("a long line fails before its end arrives", async () => {
  const input = new PassThrough();
  const { channel: reader } = channel(input);
  input.write("x".repeat(MAX_LINE_BYTES + 2));
  await assert.rejects(reader.receive(), ProtocolError);
  input.write("\n{}\n");
  await assert.rejects(reader.receive(), ProtocolError);
});

for (const line of ["{", "[1, 2]", '"text"', "null", "{} {}", Buffer.from([0xff, 0xfe])]) {
  test(`malformed line ${JSON.stringify(line.toString())}`, async () => {
    await assert.rejects(fed(line, "\n").receive(), ProtocolError);
  });
}

test("a failing input is a protocol error", async () => {
  const input = new PassThrough();
  const { channel: reader } = channel(input);
  input.destroy(new Error("broken pipe"));
  await assert.rejects(reader.receive(), /input failed: broken pipe/);
});

test("send writes one compact UTF-8 line", async () => {
  const input = new PassThrough();
  const { channel: writer, written } = channel(input);
  await writer.send({ type: "move", v: 1, info: { text: "Läufer\nopfer ♗" } });
  await writer.send({ type: "resign", v: 1 });
  assert.deepEqual(written, [
    '{"type":"move","v":1,"info":{"text":"Läufer\\nopfer ♗"}}\n',
    '{"type":"resign","v":1}\n',
  ]);
  writer.close();
  assert.ok(input.destroyed);
});
