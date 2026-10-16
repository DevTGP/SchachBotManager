// A scripted referee: plays fixed messages to a bot in this process and collects its answers.
import { Readable } from "node:stream";

import type { Bot } from "../src/bot.ts";
import { Channel } from "../src/channel.ts";
import type { Message } from "../src/channel.ts";
import { Game } from "../src/game.ts";

/** Plays the messages to the bot and returns its answers. */
export async function play(bot: Bot, ...messages: Message[]): Promise<Message[]> {
  const data = messages.map((message) => `${JSON.stringify(message)}\n`).join("");
  const input = Readable.from([Buffer.from(data)]);
  const lines: string[] = [];
  const write = (line: string): Promise<void> => {
    lines.push(line);
    return Promise.resolve();
  };
  await new Game(bot, new Channel(input, write, () => undefined)).play();
  return lines.map((line) => {
    if (!line.endsWith("\n") || line.slice(0, -1).includes("\n")) {
      throw new Error(`not one line: ${JSON.stringify(line)}`);
    }
    return JSON.parse(line) as Message;
  });
}

/** A turn message with the fields the tests vary. */
export function turn(fen: string, ply: number, lastMove: string | null = null): Message {
  return {
    type: "turn",
    v: 1,
    last_move: lastMove,
    fen,
    ply,
    remaining_ms: 1000,
    opponent_remaining_ms: 2000,
  };
}
