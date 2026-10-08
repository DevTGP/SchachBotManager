import { type ChangeEvent, type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router";

import { fetchOwnBots, uploadBot } from "../../api/bots";
import { ApiContent } from "../../components/ApiContent";
import { FormError } from "../../components/FormError";
import { useApi } from "../../hooks/useApi";
import { useSubmit } from "../../hooks/useSubmit";
import {
  entryCandidates,
  type Selection,
  selectFiles,
  selectionProblem,
} from "../../upload/selection";
import { NAME, parseVersion, suggestVersion } from "../../upload/version";
import { OwnBotsTable } from "./OwnBotsTable";
import { SelectedFiles } from "./SelectedFiles";

/** Browsers only offer a folder with this attribute, which React does not know. */
function chooseFolders(input: HTMLInputElement | null) {
  input?.setAttribute("webkitdirectory", "");
}

/** Upload of a Python bot as a folder of sources (E91, E92); the own bots below. */
export function UploadPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const ownBots = useApi(fetchOwnBots, "own-bots");
  const { pending, error, submit, fail } = useSubmit();
  const [selection, setSelection] = useState<Selection>();
  const [entryChoice, setEntryChoice] = useState<string>();
  const [name, setName] = useState("");
  const [versionInput, setVersionInput] = useState<string>();

  const candidates = selection ? entryCandidates(selection.files) : [];
  const entry = entryChoice && candidates.includes(entryChoice) ? entryChoice : candidates[0];
  const version = versionInput ?? suggestVersion(ownBots.data ?? [], name);
  const ownNames = [...new Set(ownBots.data?.map((bot) => bot.name))];

  function onFiles(event: ChangeEvent<HTMLInputElement>) {
    setSelection(selectFiles(Array.from(event.target.files ?? [])));
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
        entry,
        files: files.map((file) => ({ path: file.path, content: file.file })),
      });
      await navigate(`/bots/${bot.id}`);
    });
  }

  return (
    <>
      <h1>{t("upload.title")}</h1>
      <p>{t("upload.intro")}</p>
      <form className="form" onSubmit={onSubmit}>
        <label>
          {t("upload.folder")}
          <input type="file" multiple ref={chooseFolders} onChange={onFiles} />
        </label>
        <label>
          {t("upload.singleFiles")}
          <input type="file" multiple accept=".py" onChange={onFiles} />
        </label>
        {selection && <SelectedFiles selection={selection} />}
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
        <p className="hint">{t("upload.limit")}</p>
        <FormError error={error} />
        <button type="submit" className="primary" disabled={pending}>
          {t("upload.submit")}
        </button>
      </form>

      <h2>{t("upload.ownTitle")}</h2>
      <ApiContent state={ownBots}>{(bots) => <OwnBotsTable bots={bots} />}</ApiContent>
    </>
  );
}
