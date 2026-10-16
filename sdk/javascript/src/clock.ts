// Clock (spec/api/clock.json): the time situation of the current turn.
import { performance } from "node:perf_hooks";

/**
 * Local view of the times from turn; the referee's clock is authoritative. Elapsed time is
 * measured with a monotonic clock from the creation of the object, which the SDK does right
 * after receiving turn.
 */
export class Clock {
  readonly #start = performance.now();
  readonly #remainingMs: number;
  readonly #opponentRemainingMs: number;
  readonly #incrementMs: number;

  constructor(remainingMs: number, opponentRemainingMs: number, incrementMs: number) {
    this.#remainingMs = remainingMs;
    this.#opponentRemainingMs = opponentRemainingMs;
    this.#incrementMs = incrementMs;
  }

  /** Own remaining time at the start of this turn; does not decrease while thinking. */
  remainingMs(): number {
    return this.#remainingMs;
  }

  /** Remaining time of the opponent. */
  opponentRemainingMs(): number {
    return this.#opponentRemainingMs;
  }

  /** Time added after each own move. */
  incrementMs(): number {
    return this.#incrementMs;
  }

  /** Time spent on this turn so far; keep a margin for the transport. */
  elapsedMs(): number {
    return Math.floor(performance.now() - this.#start);
  }

  toString(): string {
    return (
      `Clock(remainingMs=${this.#remainingMs}, ` +
      `opponentRemainingMs=${this.#opponentRemainingMs}, incrementMs=${this.#incrementMs})`
    );
  }
}
