/** A required number as typed; the form converts it and the API checks the range. */
export function NumberField({
  label,
  value,
  step,
  min = 0,
  max,
  onChange,
}: {
  label: string;
  value: string;
  step?: string;
  min?: number;
  max?: number;
  onChange: (value: string) => void;
}) {
  return (
    <label>
      {label}
      <input
        type="number"
        required
        min={min}
        max={max}
        step={step}
        inputMode="decimal"
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}
