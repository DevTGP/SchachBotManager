import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

const CONFIRM_MS = 2_000;

/** Copies text to the clipboard and says so for a moment. */
export function CopyButton({ text, label }: { text: string; label: string }) {
  const { t } = useTranslation();
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!copied) return;
    const timer = window.setTimeout(() => setCopied(false), CONFIRM_MS);
    return () => window.clearTimeout(timer);
  }, [copied]);

  async function copy() {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
    } catch {
      // Without clipboard access (insecure origin, denied) the button just does nothing.
    }
  }

  return (
    <button type="button" onClick={() => void copy()}>
      {copied ? t("viewer.copied") : label}
    </button>
  );
}
