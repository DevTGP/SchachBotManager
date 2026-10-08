import { useTranslation } from "react-i18next";

const PIECES = ["q", "r", "b", "n"] as const;

/** Which piece the pawn becomes; the choices are the legal promotion moves. */
export function PromotionChoice({
  choices,
  onChoose,
  onCancel,
}: {
  choices: string[];
  onChoose: (uci: string) => void;
  onCancel: () => void;
}) {
  const { t } = useTranslation();
  return (
    <div className="promotion" role="group" aria-label={t("play.promotion")}>
      <span>{t("play.promotion")}</span>
      {PIECES.map((piece) => {
        const move = choices.find((choice) => choice.endsWith(piece));
        return (
          move && (
            <button key={piece} type="button" onClick={() => onChoose(move)}>
              {t(`play.piece.${piece}`)}
            </button>
          )
        );
      })}
      <button type="button" onClick={onCancel}>
        {t("play.cancel")}
      </button>
    </div>
  );
}
