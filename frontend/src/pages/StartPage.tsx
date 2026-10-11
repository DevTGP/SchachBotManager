import { useTranslation } from "react-i18next";

import { Board } from "../viewer/Board";

/** Italian game after 3…Bc5 4.c3: a quiet, familiar picture for the head of the page. */
const HERO_FEN = "r1bqk1nr/pppp1ppp/2n5/2b1p3/2B1P3/2P2N2/PP1P1PPP/RNBQK2R b KQkq - 0 4";
const HERO_MOVE = "c2c3";

const STEPS = ["write", "test", "upload", "compete"] as const;
const FEATURES = ["core", "fair", "sandbox", "public", "human", "remote"] as const;

const SAMPLE = `import random

import sbm


class MyBot(sbm.Bot):
    def choose_move(self, board, clock):
        return random.choice(board.legal_moves())


sbm.run(MyBot)`;

/**
 * The start page explains the idea of the project and offers no functions of its own yet (D1,
 * E166): what a bot is, how it gets onto the server and what happens there.
 */
export function StartPage() {
  const { t } = useTranslation();
  return (
    <div className="landing">
      <section className="landing-hero">
        <div>
          <h1>{t("start.title")}</h1>
          <p className="landing-lead">{t("start.lead")}</p>
          <p>{t("start.idea")}</p>
        </div>
        <div className="landing-board" aria-hidden="true">
          <Board fen={HERO_FEN} lastMove={HERO_MOVE} orientation="white" />
        </div>
      </section>

      <section>
        <h2>{t("start.stepsTitle")}</h2>
        <ol className="landing-steps">
          {STEPS.map((step) => (
            <li key={step}>
              <h3>{t(`start.steps.${step}.title`)}</h3>
              <p>{t(`start.steps.${step}.text`)}</p>
            </li>
          ))}
        </ol>
      </section>

      <section className="landing-split">
        <div>
          <h2>{t("start.codeTitle")}</h2>
          <p>{t("start.codeText")}</p>
          <p className="muted">{t("start.languages")}</p>
        </div>
        <pre className="landing-code">
          <code>{SAMPLE}</code>
        </pre>
      </section>

      <section>
        <h2>{t("start.flowTitle")}</h2>
        <div className="landing-flow" role="img" aria-label={t("start.flowLabel")}>
          <span className="landing-node">{t("start.flow.white")}</span>
          <span className="landing-arrow">⇄</span>
          <span className="landing-node referee">{t("start.flow.referee")}</span>
          <span className="landing-arrow">⇄</span>
          <span className="landing-node">{t("start.flow.black")}</span>
        </div>
        <p>{t("start.flowText")}</p>
      </section>

      <section>
        <h2>{t("start.featuresTitle")}</h2>
        <ul className="landing-features">
          {FEATURES.map((feature) => (
            <li key={feature}>
              <h3>{t(`start.features.${feature}.title`)}</h3>
              <p>{t(`start.features.${feature}.text`)}</p>
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}
