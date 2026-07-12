import { SOCIAL_FIELDS } from "../constants";


export function SocialStep({ answers, onChange }) {
  return (
    <div className="social-grid">
      {SOCIAL_FIELDS.map(([field, , label]) => (
        <div className="field-stack" key={field}>
          <label htmlFor={field}>{label}</label>
          <input
            id={field}
            data-testid={field}
            type="url"
            value={answers[field]}
            placeholder={`https://${field === "social_twitter" ? "x.com" : `${label.toLowerCase()}.com`}/…`}
            onChange={(event) => onChange(field, event.target.value)}
          />
        </div>
      ))}
    </div>
  );
}
