import { useState } from "react";
import { useTranslation } from "react-i18next";

import { fetchRatingHistory } from "../../api/botHistory";
import type { DisciplineRatingHistory } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { useApi } from "../../hooks/useApi";
import { chart, ratingValues } from "./ratingChart";

const BOX = { width: 600, height: 200, padding: 16 };
/** Beyond this many games the line alone is drawn, without a dot per game. */
const MAX_DOTS = 150;

/** The rating of the bot over its counted games, one discipline at a time (E140). */
export function BotRatingChart({ botId }: { botId: string }) {
  const { t } = useTranslation();
  const history = useApi((signal) => fetchRatingHistory(botId, signal), `rating-history:${botId}`);
  const [chosen, setChosen] = useState("");
  return (
    <section>
      <h2>{t("bot.ratingHistory")}</h2>
      <ApiContent state={history}>
        {(items) => {
          if (items.length === 0) return <p className="muted">{t("bot.noRatingHistory")}</p>;
          const shown = items.find((item) => item.discipline_id === chosen) ?? items[0]!;
          return (
            <>
              {items.length > 1 && (
                <div className="filters">
                  <label>
                    {t("matches.discipline")}
                    <select
                      value={shown.discipline_id}
                      onChange={(event) => setChosen(event.target.value)}
                    >
                      {items.map((item) => (
                        <option key={item.discipline_id} value={item.discipline_id}>
                          {item.name}
                        </option>
                      ))}
                    </select>
                  </label>
                </div>
              )}
              <RatingCurve history={shown} />
            </>
          );
        }}
      </ApiContent>
    </section>
  );
}

function RatingCurve({ history }: { history: DisciplineRatingHistory }) {
  const { t } = useTranslation();
  const values = ratingValues(history.games);
  const { points, low, high } = chart(values, BOX);
  const games = history.games.length;
  const summary = t("bot.ratingSummary", {
    value: values[values.length - 1],
    games,
    high: Math.max(...values),
    low: Math.min(...values),
  });
  return (
    <figure className="rating-chart">
      <svg
        viewBox={`0 0 ${BOX.width} ${BOX.height}`}
        role="img"
        aria-label={t("bot.ratingChartLabel", { discipline: history.name, games })}
      >
        <line
          className="frame"
          x1={BOX.padding}
          x2={BOX.width - BOX.padding}
          y1={BOX.padding}
          y2={BOX.padding}
        />
        <line
          className="frame"
          x1={BOX.padding}
          x2={BOX.width - BOX.padding}
          y1={BOX.height - BOX.padding}
          y2={BOX.height - BOX.padding}
        />
        <text x={BOX.padding} y={BOX.padding - 4}>
          {Math.round(high)}
        </text>
        <text x={BOX.padding} y={BOX.height - 2}>
          {Math.round(low)}
        </text>
        <polyline points={points.map((point) => `${point.x},${point.y}`).join(" ")} />
        {points.length <= MAX_DOTS &&
          points.map((point, index) => (
            <circle key={index} cx={point.x} cy={point.y} r={3}>
              <title>
                {index === 0
                  ? t("bot.ratingStart", { value: point.value })
                  : t("bot.ratingAfter", { game: index, value: point.value })}
              </title>
            </circle>
          ))}
      </svg>
      <figcaption className="muted">{summary}</figcaption>
    </figure>
  );
}
