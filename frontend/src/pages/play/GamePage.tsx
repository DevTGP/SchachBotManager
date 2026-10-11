import { useTranslation } from "react-i18next";
import { Link, useParams } from "react-router";

import { loadSeat } from "../../play/seats";
import type { SocketFactory } from "../../play/usePlayGame";
import { useSession } from "../../session/sessionContext";
import { CompetitionGame } from "./CompetitionGame";
import { Game } from "./Game";

/**
 * A game of the person in the browser (E114): one started on /play has its seat in this browser;
 * a league or tournament game of the own account first waits for the click on "ready" (E183).
 */
export function GamePage({ createSocket }: { createSocket?: SocketFactory }) {
  const { t } = useTranslation();
  const { user } = useSession();
  const { id = "" } = useParams();
  const seat = loadSeat(id);
  if (seat) return <Game matchId={id} seat={seat} createSocket={createSocket} />;
  if (user) return <CompetitionGame matchId={id} createSocket={createSocket} />;
  if (user === undefined) return null;
  return (
    <>
      <h1>{t("play.title")}</h1>
      <p className="error" role="alert">
        {t("play.noSeat")}
      </p>
      <Link to="/play">{t("play.newGame")}</Link>
    </>
  );
}
