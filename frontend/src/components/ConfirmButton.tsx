import { useState } from "react";

/**
 * A destructive action in two clicks (G1, E168): the first turns the button red and asks, the
 * second acts.
 */
export function ConfirmButton({
  label,
  confirmLabel,
  onConfirm,
  disabled,
  small,
  title,
}: {
  label: string;
  confirmLabel: string;
  onConfirm: () => void;
  disabled?: boolean;
  small?: boolean;
  title?: string;
}) {
  const [asking, setAsking] = useState(false);
  const size = small ? "small " : "";
  return asking ? (
    <button
      type="button"
      className={`${size}danger confirm`}
      disabled={disabled}
      onClick={onConfirm}
    >
      {confirmLabel}
    </button>
  ) : (
    <button
      type="button"
      className={`${size}danger`}
      disabled={disabled}
      title={title}
      onClick={() => setAsking(true)}
    >
      {label}
    </button>
  );
}
