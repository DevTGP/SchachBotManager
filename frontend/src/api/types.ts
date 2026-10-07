import type { components } from "./schema";

type Schemas = components["schemas"];

export type Bot = Schemas["Bot"];
export type Discipline = Schemas["Discipline"];
export type ErrorCode = Schemas["Error"]["code"];
export type Match = Schemas["Match"];
export type MatchPage = Schemas["MatchPage"];
export type MatchStatus = Schemas["MatchStatus"];
export type MatchSummary = Schemas["MatchSummary"];
export type Move = Schemas["Move"];
export type MoveInfo = NonNullable<Move["info"]>;
export type Queue = Schemas["Queue"];
export type QueueEntry = Schemas["QueueEntry"];
export type Side = Schemas["Side"];
export type Termination = Schemas["termination"];
