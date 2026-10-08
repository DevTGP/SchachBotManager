import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { createToken, fetchTokens, revokeToken } from "../../api/account";
import type { CreatedApiToken } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { CopyButton } from "../../components/CopyButton";
import { FormError } from "../../components/FormError";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";

/** Tokens for a local bot that plays against bots on the server (coders, E116). */
export function ApiTokens() {
  const { t } = useTranslation();
  const locale = useLocale();
  const tokens = useApi((signal) => fetchTokens(signal), "tokens");
  const create = useSubmit();
  const revoke = useSubmit();
  const [name, setName] = useState("");
  const [created, setCreated] = useState<CreatedApiToken | undefined>(undefined);

  function onCreate(event: FormEvent) {
    event.preventDefault();
    void create.submit(async () => {
      setCreated(await createToken(name.trim()));
      setName("");
      tokens.reload();
    });
  }

  function onRevoke(id: string) {
    void revoke.submit(async () => {
      await revokeToken(id);
      if (created?.id === id) setCreated(undefined);
      tokens.reload();
    });
  }

  return (
    <section>
      <h2>{t("tokens.title")}</h2>
      <p className="hint">{t("tokens.intro")}</p>
      {created && (
        <section className="link-box" role="status">
          <p>
            <strong>{t("tokens.created", { name: created.name })}</strong>
          </p>
          <div className="link-row">
            <input readOnly value={created.token} aria-label={t("tokens.token")} />
            <CopyButton text={created.token} label={t("tokens.copy")} />
          </div>
          <p className="muted small">{t("tokens.onlyOnce")}</p>
        </section>
      )}
      <ApiContent state={tokens}>
        {(list) =>
          list.length === 0 ? (
            <p className="muted">{t("tokens.none")}</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>{t("tokens.name")}</th>
                  <th>{t("tokens.createdAt")}</th>
                  <th>{t("tokens.lastUsed")}</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {list.map((token) => (
                  <tr key={token.id}>
                    <td>{token.name}</td>
                    <td>{formatDateTime(token.created_at, locale)}</td>
                    <td>
                      {token.last_used_at
                        ? formatDateTime(token.last_used_at, locale)
                        : t("tokens.never")}
                    </td>
                    <td>
                      <button
                        type="button"
                        onClick={() => onRevoke(token.id)}
                        disabled={revoke.pending}
                      >
                        {t("tokens.revoke")}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )
        }
      </ApiContent>
      <FormError error={revoke.error} />
      <form className="form" onSubmit={onCreate}>
        <label>
          {t("tokens.name")}
          <input
            required
            maxLength={40}
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>
        <FormError error={create.error} rules="tokenError" />
        <button type="submit" className="primary" disabled={create.pending}>
          {t("tokens.create")}
        </button>
      </form>
    </section>
  );
}
