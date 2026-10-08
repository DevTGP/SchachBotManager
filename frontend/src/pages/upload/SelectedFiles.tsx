import { useTranslation } from "react-i18next";

import type { Selection } from "../../upload/selection";

/** What will be uploaded, and what stays at home. */
export function SelectedFiles({ selection }: { selection: Selection }) {
  const { t } = useTranslation();
  return (
    <div>
      <p>{t("upload.fileCount", { count: selection.files.length })}</p>
      <ul className="file-list">
        {selection.files.map((file) => (
          <li key={file.path}>
            <span className="info-text">{file.path}</span>{" "}
            <span className="muted">({t(`upload.${file.kind}`)})</span>
          </li>
        ))}
      </ul>
      {selection.ignored.length > 0 && (
        <p className="hint">{t("upload.ignored", { paths: selection.ignored.join(", ") })}</p>
      )}
    </div>
  );
}
