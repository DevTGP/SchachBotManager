import { type FormEvent, useState } from "react";
import { useTranslation } from "react-i18next";

import { createToken, fetchTokens, revokeToken } from "../../api/account";
import type { ApiToken, CreatedApiToken } from "../../api/types";
import { ApiContent } from "../../components/ApiContent";
import { ConfirmButton } from "../../components/ConfirmButton";
import { CopyButton } from "../../components/CopyButton";
import { FormError } from "../../components/FormError";
import { TableShell } from "../../components/TableShell";
import { formatDateTime } from "../../format/dateTime";
import { useApi } from "../../hooks/useApi";
import { useLocale } from "../../hooks/useLocale";
import { useSubmit } from "../../hooks/useSubmit";

/** The command that plays a local bot against a bot of this site (E116). */
function remoteCommand(token: string): string {
  return `SBM_TOKEN=${token} python bot.py --remote ${window.location.origin} --opponent NAME`;
}

/** Tokens for a local bot that plays against bots on the server (coders, E116, G7). */
export function ApiTokens() {
  const { t } = useTranslation();
  const tokens = useApi((signal) => fetchTokens(signal), "tokens");
  const create = useSubmit();
  const [name, setName] = useState("");
  const [created, setCreated] = useState<CreatedApiToken | undefined>(undefined);
  const command = remoteCommand(created?.token ?? "sbm_…");

  function onCreate(event: FormEvent) {
    event.preventDefault();
    void create.submit(async () => {
      setCreated(await createToken(name.trim()));
      setName("");
      tokens.reload();
    });
  }

  function onRevoked(id: string) {
    if (created?.id === id) setCreated(undefined);
    tokens.reload();
  }

  return (
    <section>
      <h2>{t("tokens.title")}</h2>
      <p className="hint">{t("tokens.intro")}</p>
      <div className="command-box">
        <pre>
          <code>{command}</code>
        </pre>
        <CopyButton text={command} label={t("tokens.copyCommand")} />
      </div>
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
        {(list) => <TokenTable tokens={list} onRevoked={onRevoked} />}
      </ApiContent>
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

/** The tokens with a revoke that asks once more (G1). */
function TokenTable({
  tokens,
  onRevoked,
}: {
  tokens: ApiToken[];
  onRevoked: (id: string) => void;
}) {
  const { t } = useTranslation();
  const locale = useLocale();
  const { pending, error, submit } = useSubmit();

  function revoke(id: string) {
    void submit(async () => {
      await revokeToken(id);
      onRevoked(id);
    });
  }

  return (
    <>
      <TableShell rows={tokens.length} empty={t("tokens.none")}>
        <thead>
          <tr>
            <th>{t("tokens.name")}</th>
            <th>{t("tokens.createdAt")}</th>
            <th className="optional">{t("tokens.lastUsed")}</th>
            <th>
              <span className="sr-only">{t("common.actions")}</span>
            </th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((token) => (
            <tr key={token.id}>
              <td>{token.name}</td>
              <td>{formatDateTime(token.created_at, locale)}</td>
              <td className="optional">
                {token.last_used_at
                  ? formatDateTime(token.last_used_at, locale)
                  : t("tokens.never")}
              </td>
              <td className="row-actions">
                <ConfirmButton
                  small
                  label={t("tokens.revoke")}
                  confirmLabel={t("tokens.revokeConfirm")}
                  onConfirm={() => revoke(token.id)}
                  disabled={pending}
                />
              </td>
            </tr>
          ))}
        </tbody>
      </TableShell>
      <FormError error={error} />
    </>
  );
}
