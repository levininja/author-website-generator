export function ColorField({ id, label, value, onChange }) {
  return (
    <div className="color-field">
      <div
        className="color-preview"
        data-testid={`${id}-color-preview`}
        style={{ backgroundColor: value }}
        aria-hidden="true"
      />
      <div className="color-controls">
        <label htmlFor={`${id}-picker`}>{label}</label>
        <div className="color-control-row">
          <input
            id={`${id}-picker`}
            data-testid={`${id}-color-picker`}
            type="color"
            value={value}
            onChange={(event) => onChange(event.target.value)}
          />
          <input
            aria-label={`${label} hex value`}
            data-testid={`${id}-color-hex`}
            type="text"
            value={value}
            pattern="^#[0-9a-fA-F]{6}$"
            onChange={(event) => {
              if (/^#[0-9a-fA-F]{6}$/.test(event.target.value)) {
                onChange(event.target.value);
              }
            }}
          />
        </div>
      </div>
    </div>
  );
}
