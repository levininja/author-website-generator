import { useEffect, useState } from "react";

import { IMAGE_TYPES } from "../constants";


export function HeadshotStep({ value, onChange }) {
  const [previewUrl, setPreviewUrl] = useState("");

  useEffect(() => {
    if (!(value instanceof File)) {
      setPreviewUrl("");
      return undefined;
    }

    const objectUrl = URL.createObjectURL(value);
    setPreviewUrl(objectUrl);
    return () => URL.revokeObjectURL(objectUrl);
  }, [value]);

  return (
    <div className="field-stack">
      <label htmlFor="author-headshot">
        Author photo
        <span className="optional-label"> Optional</span>
      </label>
      <input
        id="author-headshot"
        data-testid="author-headshot"
        type="file"
        accept={IMAGE_TYPES.join(",")}
        onChange={(e) => onChange(e.target.files[0] || null)}
      />
      <span className="field-hint">JPG, PNG, or WebP; maximum 10 MB.</span>
      {previewUrl && (
        <div className="selected-image" role="status">
          <img src={previewUrl} alt="Selected author photo preview" />
          <div className="selected-image-copy">
            <strong><span aria-hidden="true">✓</span> Photo selected</strong>
            <span>{value.name}</span>
          </div>
        </div>
      )}
    </div>
  );
}
