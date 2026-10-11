/** One choice of a pill select; value "" stands for "all" or the default. */
export interface Pill<T extends string> {
  value: T;
  label: string;
}

/** A small set of choices as a row of toggle buttons instead of a dropdown (E168). */
export function PillSelect<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string;
  options: readonly Pill<T>[];
  value: T;
  onChange: (value: T) => void;
}) {
  return (
    <div className="pill-field">
      <span className="pill-label">{label}</span>
      <div className="pills" role="group" aria-label={label}>
        {options.map((option) => (
          <button
            key={option.value}
            type="button"
            aria-pressed={option.value === value}
            onClick={() => onChange(option.value)}
          >
            {option.label}
          </button>
        ))}
      </div>
    </div>
  );
}
