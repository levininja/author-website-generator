export function Repeater({
  title,
  buttonLabel,
  testIdPrefix,
  items,
  emptyItem,
  onChange,
  renderItem,
}) {
  function add() {
    onChange([...items, { ...emptyItem }]);
  }
  function update(index, field, value) {
    onChange(items.map((item, itemIndex) => (
      itemIndex === index ? { ...item, [field]: value } : item
    )));
  }
  function remove(index) {
    onChange(items.filter((_, itemIndex) => itemIndex !== index));
  }

  return (
    <section className="nested-section">
      <h3>{title}</h3>
      {items.map((item, index) => (
        <fieldset className="nested-item" key={index}>
          <legend>{title.replace(/s$/, "")} {index + 1}</legend>
          {renderItem(item, index, update)}
          <button
            type="button"
            className="button-link danger-link"
            data-testid={`${testIdPrefix}-${index}-remove`}
            onClick={() => remove(index)}
          >
            Remove
          </button>
        </fieldset>
      ))}
      <button
        type="button"
        className="button-secondary compact-button"
        data-testid={`${testIdPrefix}-add`}
        onClick={add}
      >
        + {buttonLabel}
      </button>
    </section>
  );
}
