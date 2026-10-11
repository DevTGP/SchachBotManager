// Pages with changing data ask the API again in these intervals. A running match in the viewer
// gets its moves from the gateway's event stream instead and is asked about only without it
// (E142).

/** A queued match, or a running one without the event stream. */
export const POLL_MATCH_MS = 2_000;

/** Lists and the queue. */
export const POLL_LIST_MS = 10_000;

/** A bot in its verification. */
export const POLL_VERIFY_MS = 3_000;
