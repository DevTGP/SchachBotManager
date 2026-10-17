// Line channel to the referee: one JSON message per line (NDJSON) over stdio or TCP.
import net from "node:net";
import type { Readable } from "node:stream";

export const MAX_LINE_BYTES = 65_536;

/** The referee sent something the protocol does not allow; the SDK cannot continue. */
export class ProtocolError extends Error {
  constructor(message: string) {
    super(message);
    this.name = "ProtocolError";
  }
}

export type Message = Record<string, unknown>;

const NEWLINE = 0x0a;
const RETURN = 0x0d;

/** Splits a byte stream into lines; a line without newline at the end of input counts too. */
class LineReader {
  readonly #lines: Buffer[] = [];
  #pending: Buffer = Buffer.alloc(0);
  #ended = false;
  #failure: Error | undefined;
  #wake: (() => void) | undefined;

  constructor(stream: Readable) {
    stream.on("data", (chunk: Buffer) => this.#push(chunk));
    stream.on("end", () => {
      if (this.#pending.length > 0) {
        this.#lines.push(this.#pending);
      }
      this.#ended = true;
      this.#notify();
    });
    stream.on("error", (error: Error) => {
      this.#fail(new ProtocolError(`input failed: ${error.message}`));
    });
  }

  async next(): Promise<Buffer | null> {
    for (;;) {
      const line = this.#lines.shift();
      if (line !== undefined) {
        return line;
      }
      if (this.#failure !== undefined) {
        throw this.#failure;
      }
      if (this.#ended) {
        return null;
      }
      await new Promise<void>((resolve) => {
        this.#wake = resolve;
      });
    }
  }

  #push(chunk: Buffer): void {
    if (this.#failure !== undefined) {
      return;
    }
    let data = this.#pending.length > 0 ? Buffer.concat([this.#pending, chunk]) : chunk;
    for (let end = data.indexOf(NEWLINE); end >= 0; end = data.indexOf(NEWLINE)) {
      this.#lines.push(data.subarray(0, end));
      data = data.subarray(end + 1);
    }
    // One byte more for a carriage return before the newline.
    if (data.length > MAX_LINE_BYTES + 1) {
      this.#fail(new ProtocolError(`line longer than ${MAX_LINE_BYTES} bytes`));
      return;
    }
    this.#pending = Buffer.from(data);
    this.#notify();
  }

  #fail(error: Error): void {
    this.#failure ??= error;
    this.#pending = Buffer.alloc(0);
    this.#notify();
  }

  #notify(): void {
    const wake = this.#wake;
    this.#wake = undefined;
    wake?.();
  }
}

const decoder = new TextDecoder("utf-8", { fatal: true });

/** Reads referee messages and writes bot messages, each passed on at once. */
export class Channel {
  readonly #reader: LineReader;
  readonly #write: (line: string) => Promise<void>;
  readonly #close: () => void;

  constructor(input: Readable, write: (line: string) => Promise<void>, close: () => void) {
    this.#reader = new LineReader(input);
    this.#write = write;
    this.#close = close;
  }

  /** The next message, or null at the end of the input. */
  async receive(): Promise<Message | null> {
    const line = await this.#reader.next();
    if (line === null) {
      return null;
    }
    const content = line.at(-1) === RETURN ? line.subarray(0, -1) : line;
    if (content.length > MAX_LINE_BYTES) {
      throw new ProtocolError(`line longer than ${MAX_LINE_BYTES} bytes`);
    }
    let message: unknown;
    try {
      message = JSON.parse(decoder.decode(content));
    } catch (error) {
      throw new ProtocolError(`invalid JSON: ${(error as Error).message}`);
    }
    if (typeof message !== "object" || message === null || Array.isArray(message)) {
      throw new ProtocolError(
        `message is not a JSON object: ${content.subarray(0, 80).toString()}`,
      );
    }
    return message as Message;
  }

  send(message: Message): Promise<void> {
    return this.#write(`${JSON.stringify(message)}\n`);
  }

  close(): void {
    this.#close();
  }
}

function writer(stream: NodeJS.WritableStream): (line: string) => Promise<void> {
  // Bound now, so the protocol keeps the stream's own write when openStdio replaces it.
  const write = stream.write.bind(stream);
  return (line: string) =>
    new Promise<void>((resolve, reject) => {
      write(line, (error?: Error | null) => (error ? reject(error) : resolve()));
    });
}

/**
 * Takes stdin and stdout for the protocol and sends everything else written to process.stdout,
 * console.log included, to stderr, so nothing can corrupt the protocol stream (E225).
 */
export function openStdio(): Channel {
  const stdout = process.stdout;
  const write = writer(stdout);
  stdout.write = process.stderr.write.bind(process.stderr) as typeof stdout.write;
  const stdin = process.stdin;
  return new Channel(stdin, write, () => stdin.destroy());
}

/** Connects to the waiting arena on this machine (local debugging only). */
export async function openTcp(port: number): Promise<Channel> {
  const socket = net.connect({ host: "127.0.0.1", port });
  await new Promise<void>((resolve, reject) => {
    socket.once("connect", () => {
      socket.off("error", reject);
      resolve();
    });
    socket.once("error", reject);
  });
  socket.setNoDelay(true);
  return new Channel(socket, writer(socket), () => socket.destroy());
}
