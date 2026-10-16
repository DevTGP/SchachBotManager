import { type FormEvent, useMemo, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link, useNavigate } from "react-router";

import { fetchLimits } from "../../api/account";
import { fetchOwnBots, uploadBot } from "../../api/bots";
import { FormError } from "../../components/FormError";
import { PillSelect } from "../../components/PillSelect";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import {
  detectLanguage,
  entryCandidates,
  type FoundFile,
  selectionProblem,
  selectPaths,
  sourceSuffixes,
  UPLOAD_LANGUAGES,
  type UploadLanguage,
} from "../../upload/selection";
import { NAME, parseVersion, suggestVersion } from "../../upload/version";
import { DESCRIPTION_LENGTH } from "../bot/BotDescription";
import { FileDrop } from "./FileDrop";

/** Upload of a bot as a folder of sources (E91, E92, E227); the own bots are on "My bots". */
export function UploadPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const ownBots = useApi(fetchOwnBots, "own-bots");
  const limits = useApi(fetchLimits, "own-limits");
  const { pending, error, submit, fail } = useSubmit();
  const [language, setLanguage] = useState<UploadLanguage>("python");
  const [found, setFound] = useState<FoundFile[]>();
  const [entryChoice, setEntryChoice] = useState<string>();
  const [name, setName] = useState("");
  const [versionInput, setVersionInput] = useState<string>();
  const [description, setDescription] = useState("");

  const selection = useMemo(() => found && selectPaths(found, language), [found, language]);
  const candidates = selection ? entryCandidates(selection.files, language) : [];
  const sources = sourceSuffixes(language);
  const entry = entryChoice && candidates.includes(entryChoice) ? entryChoice : candidates[0];
  const version = versionInput ?? suggestVersion(ownBots.data ?? [], name);
  const ownNames = [...new Set(ownBots.data?.map((bot) => bot.name))];

  // Files of only one language switch to it; the choice stays free.
  function onFound(files: FoundFile[]) {
    setFound(files);
    setLanguage((current) => detectLanguage(files) ?? current);
  }

  function onSubmit(event: FormEvent) {
    event.preventDefault();
    const files = selection?.files ?? [];
    const problem = selectionProblem(files);
    if (problem) return fail(problem);
    if (!entry) return fail("upload.noEntry");
    if (!NAME.test(name)) return fail("fieldError.name");
    if (!parseVersion(version)) return fail("fieldError.version");
    void submit(async () => {
      const bot = await uploadBot({
        name,
        version,
        language,
        entry,
        description,
        files: files.map((file) => ({ path: file.path, content: file.file })),
      });
      await navigate(`/bots/${bot.id}`);
    });
  }

  return (
    <>
      <h1>{t("upload.title")}</h1>
      <p>{t("upload.intro", { sources })}</p>
      <form className="form" onSubmit={onSubmit}>
        <PillSelect
          label={t("upload.language")}
          options={UPLOAD_LANGUAGES.map((code) => ({ value: code, label: t(`language.${code}`) }))}
          value={language}
          onChange={setLanguage}
        />
        <FileDrop language={language} selection={selection} onFound={onFound} />
        {candidates.length > 0 && (
          <label>
            {t("upload.entry")}
            <select value={entry} onChange={(event) => setEntryChoice(event.target.value)}>
              {candidates.map((path) => (
                <option key={path} value={path}>
                  {path}
                </option>
              ))}
            </select>
          </label>
        )}
        <label>
          {t("upload.name")}
          <input
            required
            list="own-bot-names"
            autoComplete="off"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
          <span className="hint">{t("upload.nameHint")}</span>
        </label>
        <datalist id="own-bot-names">
          {ownNames.map((ownName) => (
            <option key={ownName} value={ownName} />
          ))}
        </datalist>
        <label>
          {t("upload.version")}
          <input
            required
            placeholder="1.0.0"
            value={version}
            onChange={(event) => setVersionInput(event.target.value)}
          />
          <span className="hint">{t("upload.versionHint")}</span>
        </label>
        <label>
          {t("bot.description")}
          <textarea
            rows={4}
            maxLength={DESCRIPTION_LENGTH}
            value={description}
            onChange={(event) => setDescription(event.target.value)}
          />
          <span className="hint">{t("bot.descriptionHint", { max: DESCRIPTION_LENGTH })}</span>
        </label>
        <p className="hint">
          {t("upload.review")}
          {limits.data && ` ${t("upload.limit", { uploads: limits.data.uploads_per_day })}`}
        </p>
        <FormError error={error} values={{ sources }} />
        <button type="submit" className="primary" disabled={pending}>
          {t("upload.submit")}
        </button>
      </form>
      <p>
        <Link to="/account/bots">{t("upload.ownLink")}</Link>
      </p>
    </>
  );
}
