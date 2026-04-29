function normalize(value) {
  return value.trim().toLowerCase().replace(/\s+/g, " ");
}

function findSuggestion(name, suggestions) {
  const normalized = normalize(name);
  const match = suggestions.find((item) => normalize(item.name) === normalized);
  return match ? { label: match.name, lat: match.lat, lng: match.lng } : null;
}

function CoordinateInput({ label, value, onChange, invalid, suggestions, onSearch }) {
  return (
    <div className="field-group">
      <label className="field">
        <span>{label} name</span>
        <input
          list={`${label}-locations`}
          value={value.label}
          onChange={(event) => {
            const key = event.target.value;
            onSearch(key);
            const suggestion = findSuggestion(key, suggestions);
            if (suggestion) {
              onChange(suggestion);
              return;
            }
            onChange({ label: key, lat: "", lng: "" });
          }}
        />
        <datalist id={`${label}-locations`}>
          {suggestions.map((item) => (
            <option key={`${label}-${item.name}-${item.lat}-${item.lng}`} value={item.name} />
          ))}
        </datalist>
        {invalid ? <small className="field-error">Enter any Bengaluru place name or valid latitude/longitude.</small> : null}
      </label>
      <label className="field">
        <span>Latitude</span>
        <input
          type="number"
          step="0.0001"
          value={value.lat}
          onChange={(event) => onChange({ ...value, lat: event.target.value === "" ? "" : Number(event.target.value) })}
        />
      </label>
      <label className="field">
        <span>Longitude</span>
        <input
          type="number"
          step="0.0001"
          value={value.lng}
          onChange={(event) => onChange({ ...value, lng: event.target.value === "" ? "" : Number(event.target.value) })}
        />
      </label>
    </div>
  );
}

export default function SearchPanel({
  origin,
  destination,
  vehicleType,
  optimizeFor,
  onOriginChange,
  onDestinationChange,
  onVehicleChange,
  onOptimizeChange,
  onSubmit,
  loading,
  invalidOrigin,
  invalidDestination,
  originSuggestions,
  destinationSuggestions,
  onOriginSearch,
  onDestinationSearch,
}) {
  return (
    <section className="panel glass">
      <div className="panel-heading">
        <div>
          <p className="eyebrow">Trip planner</p>
          <h2>Find the best Bangalore route</h2>
        </div>
        <p className="muted">Fastest, shortest, or greenest with traffic and weather awareness.</p>
      </div>

      <CoordinateInput
        label="Origin"
        value={origin}
        onChange={onOriginChange}
        invalid={invalidOrigin}
        suggestions={originSuggestions}
        onSearch={onOriginSearch}
      />
      <CoordinateInput
        label="Destination"
        value={destination}
        onChange={onDestinationChange}
        invalid={invalidDestination}
        suggestions={destinationSuggestions}
        onSearch={onDestinationSearch}
      />

      <div className="field-row">
        <label className="field">
          <span>Optimization goal</span>
          <select value={optimizeFor} onChange={(event) => onOptimizeChange(event.target.value)}>
            <option value="time">Fastest</option>
            <option value="distance">Shortest distance</option>
            <option value="eco">Greenest</option>
          </select>
        </label>
        <label className="field">
          <span>Vehicle type</span>
          <select value={vehicleType} onChange={(event) => onVehicleChange(event.target.value)}>
            <option value="car">Car</option>
            <option value="bike">Bike</option>
            <option value="truck">Truck</option>
          </select>
        </label>
      </div>

      <button type="button" className="primary-button" onClick={onSubmit} disabled={loading}>
        {loading ? "Calculating..." : "Calculate route"}
      </button>
    </section>
  );
}
