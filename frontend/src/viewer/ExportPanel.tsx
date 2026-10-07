import { useTranslation } from "react-i18next";

import { matchPgnUrl } from "../api/endpoints";
import { CopyButton } from "../components/CopyButton";

/** PGN of the whole match, FEN of the shown position and a link to it. */
export function ExportPanel({ matchId, fen, ply }: { matchId: string; fen: string; ply: number }) {
  const { t } = useTranslation();
  const link = `${window.location.origin}/matches/${matchId}?ply=${ply}`;
  return (
    <div className="export">
      <a className="button" href={matchPgnUrl(matchId)} download>
        {t("viewer.pgn")}
      </a>
      <CopyButton text={fen} label={t("viewer.copyFen")} />
      <CopyButton text={link} label={t("viewer.copyLink")} />
    </div>
  );
}
