import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "react-router";

import { declareReady, fetchCompetitionGames } from "../../api/competitionGames";
import type { CompetitionGame as Item, SideReadiness } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { competitionName } from "../../format/competition";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { loadSeat, saveSeat } from "../../play/seats";
import type { SocketFactory } from "../../play/usePlayGame";
import { DeadlineCountdown } from "./DeadlineCountdown";
import { Game } from "./Game";
import { StartCountdown } from "./StartCountdown";

// The runner starts a game once both sides are ready and present; presence lasts 45 s (E183).
const POLL_MS = 5_000;
const PING_MS = 15_000;

/**
 * A league or tournament game of the own account: "ready" by click, kept present while the page
 * is open, then played on the board like a game from /play (E183).
 */
export function CompetitionGame({
  matchId,
  createSocket,
}: {
  matchId: string;
  createSocket?: SocketFactory;
}) {
  const { t } = useTranslation();
  const [started, setStarted] = useState(false);
  const games = useApi(
    (signal) => fetchCompetitionGames(signal),
    "account/competition-games",
    started ? undefined : POLL_MS,
  );
  const item = games.data?.find((game) => game.match.id === matchId);
  const startedNow = item !== undefined && hasStarted(item);
  // Once on the board the game stays there, also after it ended and left the list.
  if (startedNow && !started) setStarted(true);

  if (started) {
    const seat = loadSeat(matchId, "ready");
    if (seat) return <Game matchId={matchId} seat={seat} competition createSocket={createSocket} />;
    return <Notice text={t("play.noSeat")} matchId={matchId} />;
  }
  return (
    <ApiContent state={games}>
      {() =>
        item ? (
          <Waiting item={item} onReady={games.reload} />
        ) : (
          <Notice text={t("competitionGame.notOpen")} matchId={matchId} />
        )
      }
    </ApiContent>
  );
}

function hasStarted(item: Item): boolean {
  return item.match.status !== "queued" || item.match.readiness?.started_at != null;
}

function Waiting({ item, onReady }: { item: Item; onReady: () => void }) {
  const { t, i18n } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [clicked, setClicked] = useState(false);
  const { match, color } = item;
  const readiness = match.readiness;
  const own = readiness?.[color];
  const ready = readiness != null && (clicked || own?.ready === true);
  usePresence(match.id, ready);

  function onClick() {
    void submit(async () => {
      const answer = await declareReady(match.id, loadSeat(match.id, "ready"));
      saveSeat(match.id, answer.seat, "ready");
      setClicked(true);
      onReady();
    });
  }

  const other = color === "white" ? "black" : "white";
  return (
    <>
      <h1>
        {match.white.name} – {match.black.name}
      </h1>
      <p>{competitionName(t, item)}</p>
      {readiness == null ? (
        <p role="status">{t("competitionGame.notReleased")}</p>
      ) : (
        <>
          {item.estimated_start == null ? (
            <DeadlineCountdown at={readiness.deadline} />
          ) : (
            <p>
              {t("competitionGame.deadline", {
                at: formatDateTime(readiness.deadline, i18n.language),
              })}
            </p>
          )}
          <p role="status">{t(ready ? "competitionGame.youReady" : "competitionGame.notReady")}</p>
          {item.estimated_start != null && <StartCountdown at={item.estimated_start} />}
          <p>{opponentText(t, readiness[other])}</p>
          <p className="hint">{t("competitionGame.hint")}</p>
          <FormError error={error} />
          {!ready && (
            <button type="button" className="primary" disabled={pending} onClick={onClick}>
              {t("competitionGame.ready")}
            </button>
          )}
        </>
      )}
      <p>
        <Link to={`/matches/${match.id}`}>{t("competitionGame.toMatch")}</Link>
      </p>
    </>
  );
}

/** While ready, says so again now and then: the seat stays, and the account counts as present. */
function usePresence(matchId: string, ready: boolean) {
  useEffect(() => {
    if (!ready) return;
    let stopped = false;
    async function ping() {
      try {
        const answer = await declareReady(matchId, loadSeat(matchId, "ready"));
        if (!stopped) saveSeat(matchId, answer.seat, "ready");
      } catch {
        // The list shows whether the game still waits; the next ping tries again.
      }
    }
    const timer = window.setInterval(() => void ping(), PING_MS);
    // Without a seat in this browser (another browser said ready) one is needed before the start.
    if (loadSeat(matchId, "ready") === undefined) void ping();
    return () => {
      stopped = true;
      window.clearInterval(timer);
    };
  }, [matchId, ready]);
}

function opponentText(t: (key: string) => string, side: SideReadiness | null): string {
  if (side === null) return t("competitionGame.opponentBot");
  if (!side.ready) return t("competitionGame.opponentNotReady");
  return t(side.present ? "competitionGame.opponentReady" : "competitionGame.opponentAway");
}

function Notice({ text, matchId }: { text: string; matchId: string }) {
  const { t } = useTranslation();
  return (
    <>
      <h1>{t("play.title")}</h1>
      <p className="error" role="alert">
        {text}
      </p>
      <Link to={`/matches/${matchId}`}>{t("competitionGame.toMatch")}</Link>
    </>
  );
}
