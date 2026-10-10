import { useState } from "react";
import { useTranslation } from "react-i18next";

import { positionFromPgn } from "../api/positions";
import { useSubmit } from "../hooks/useSubmit";
import { FormError } from "./FormError";

/**
 * The start position as FEN, empty for the standard position; "From PGN" fills it in from a
 * game and a number of half-moves, as sbm-arena --replay does (E69, E159).
 */
export function StartPositionField({
  value,
  onChange,
}: {
  value: string;
  onChange: (fen: string) => void;
}) {
  const { t } = useTranslation();
  const { pending, error, submit } = useSubmit();
  const [pgn, setPgn] = useState("");
  const [game, setGame] = useState("1");
  const [plies, setPlies] = useState("");

  function fill() {
    void submit(async () => {
      const fen = await positionFromPgn({
        pgn,
        game: Number(game),
        plies: plies.trim() === "" ? null : Number(plies),
      });
      onChange(fen);
    });
  }

  return (
    <>
      <label>
        {t("admin.startFen")}
        <input
          value={value}
          placeholder={t("admin.startFenHint")}
          onChange={(event) => onChange(event.target.value)}
        />
      </label>
      <details className="from-pgn">
        <summary>{t("startPosition.fromPgn")}</summary>
        <label>
          {t("startPosition.pgn")}
          <textarea rows={5} value={pgn} onChange={(event) => setPgn(event.target.value)} />
        </label>
        <div className="form-row">
          <label>
            {t("startPosition.game")}
            <input
              type="number"
              min={1}
              inputMode="numeric"
              value={game}
              onChange={(event) => setGame(event.target.value)}
            />
          </label>
          <label>
            {t("startPosition.plies")}
            <input
              type="number"
              min={0}
              inputMode="numeric"
              value={plies}
              placeholder={t("startPosition.allPlies")}
              onChange={(event) => setPlies(event.target.value)}
            />
          </label>
        </div>
        <FormError error={error} rules="pgnError" />
        <button type="button" disabled={pending || pgn.trim() === ""} onClick={fill}>
          {t("startPosition.apply")}
        </button>
      </details>
    </>
  );
}
