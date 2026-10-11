import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { fetchBots, fetchDisciplines } from "../../api/endpoints";
import { startGame } from "../../api/play";
import type { Bot, PlayRequest, StoredDiscipline } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { BotPicker } from "../../components/BotPicker";
import { FormError } from "../../components/FormError";
import { ColorSelect } from "../../components/matchFields/ColorSelect";
import {
  DEFAULT_CONDITIONS,
  type MatchConditions,
  timeConditions,
} from "../../components/matchFields/conditions";
import { MatchFields } from "../../components/matchFields/MatchFields";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import { saveSeat } from "../../play/seats";
import { OwnCompetitionGames } from "./OwnCompetitionGames";

// Free times up to 30 min + 30 s (E115).
const MAX_MINUTES = 30;
const MAX_INCREMENT_SECONDS = 30;

interface SetupForm extends MatchConditions {
  bot: string;
  color: PlayRequest["color"];
}

/**
 * Choose a verified bot or a random one, a color and the time, then play in the browser (E11,
 * E114, E162). The own league and tournament games come first (E183).
 */
export function PlaySetupPage() {
  const { t } = useTranslation();
  const bots = useApi((signal) => fetchBots(signal), "bots");
  const disciplines = useApi((signal) => fetchDisciplines(signal), "disciplines");
  return (
    <>
      <h1>{t("play.title")}</h1>
      <OwnCompetitionGames />
      <p>{t("play.intro")}</p>
      <ApiContent state={bots}>
        {(list) => <SetupForm bots={list} disciplines={disciplines.data ?? []} />}
      </ApiContent>
    </>
  );
}

function SetupForm({ bots, disciplines }: { bots: Bot[]; disciplines: StoredDiscipline[] }) {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { pending, error, submit } = useSubmit();
  const [form, setForm] = useState<SetupForm>({
    ...DEFAULT_CONDITIONS.play,
    bot: bots.find((bot) => bot.builtin)?.id ?? bots[0]?.id ?? "",
    color: "random",
  });

  if (bots.length === 0) return <p className="muted">{t("play.noBots")}</p>;

  function set(patch: Partial<SetupForm>) {
    setForm((current) => ({ ...current, ...patch }));
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    void submit(async () => {
      const times = timeConditions(form, "play");
      const seat = await startGame({ bot_id: form.bot, color: form.color, ...times });
      saveSeat(seat.match_id, seat.seat);
      await navigate(`/play/${seat.match_id}`);
    });
  }

  return (
    <form className="form" onSubmit={onSubmit}>
      <div className="form-row">
        <BotPicker
          label={t("play.opponent")}
          bots={bots}
          value={form.bot}
          random
          onChange={(bot) => set({ bot })}
        />
        <ColorSelect
          label={t("play.color")}
          value={form.color}
          random
          onChange={(color) => set({ color })}
        />
      </div>
      <MatchFields
        variant="play"
        disciplines={disciplines}
        form={form}
        limits={{ initial: MAX_MINUTES, incrementSeconds: MAX_INCREMENT_SECONDS }}
        onChange={set}
      />
      <p className="hint">{t("play.limits")}</p>
      <p className="hint">{t("play.ratedHint")}</p>
      <FormError error={error} rules="playError" />
      <button type="submit" className="primary" disabled={pending}>
        {t("play.start")}
      </button>
    </form>
  );
}
