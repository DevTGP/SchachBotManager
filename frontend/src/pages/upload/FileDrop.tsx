import { type ChangeEvent, type DragEvent, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { droppedEntries, droppedFiles } from "../../upload/dropped";
import {
  type FoundFile,
  foundFiles,
  type Selection,
  sourceSuffixes,
  type UploadLanguage,
} from "../../upload/selection";
import { SelectedFiles } from "./SelectedFiles";

/** Browsers only offer a folder with this attribute, which React does not know. */
function chooseFolders(input: HTMLInputElement | null) {
  input?.setAttribute("webkitdirectory", "");
}

/**
 * One area for the sources (G16): drop a folder or files, or choose them with buttons in the
 * language of the page; the inputs themselves stay hidden (U12).
 */
export function FileDrop({
  language,
  selection,
  onFound,
}: {
  language: UploadLanguage;
  selection: Selection | undefined;
  onFound: (found: FoundFile[]) => void;
}) {
  const { t } = useTranslation();
  const folder = useRef<HTMLInputElement>(null);
  const files = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);

  function onFiles(event: ChangeEvent<HTMLInputElement>) {
    onFound(foundFiles(event.target.files ?? []));
    event.target.value = "";
  }

  function onDragOver(event: DragEvent) {
    event.preventDefault();
    setOver(true);
  }

  function onDrop(event: DragEvent) {
    event.preventDefault();
    setOver(false);
    const entries = droppedEntries(event.dataTransfer.items);
    void droppedFiles(entries).then(onFound);
  }

  return (
    <div
      className={over ? "file-drop over" : "file-drop"}
      onDragOver={onDragOver}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
    >
      <p>{t("upload.drop", { sources: sourceSuffixes(language) })}</p>
      <div className="inline-actions">
        <button type="button" onClick={() => folder.current?.click()}>
          {t("upload.chooseFolder")}
        </button>
        <button type="button" onClick={() => files.current?.click()}>
          {t("upload.chooseFiles")}
        </button>
      </div>
      <input
        ref={(input) => {
          folder.current = input;
          chooseFolders(input);
        }}
        type="file"
        multiple
        hidden
        aria-label={t("upload.chooseFolder")}
        onChange={onFiles}
      />
      <input
        ref={files}
        type="file"
        multiple
        accept={sourceSuffixes(language).replaceAll(" ", "")}
        hidden
        aria-label={t("upload.chooseFiles")}
        onChange={onFiles}
      />
      {selection && <SelectedFiles selection={selection} />}
    </div>
  );
}
