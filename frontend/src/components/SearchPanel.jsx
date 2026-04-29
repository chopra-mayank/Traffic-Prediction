import { useEffect, useRef, useState } from "react";

function LocationInput({ label, value, onChange, suggestions, onSearch, showError }) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef(null);

  const invalid = value.label.trim() !== "" && (value.lat === "" || value.lng === "");

  // filter suggestions by current input
  const filtered = value.label.trim()
    ? suggestions
        .filter((s) => s.name.toLowerCase().includes(value.label.toLowerCase()))
        .slice(0, 7)
    : suggestions.slice(0, 7);

  useEffect(() => {
    function handleOutside(e) {
      if (wrapRef.current && !wrapRef.current.contains(e.target)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handleOutside);
    return () => document.removeEventListener("mousedown", handleOutside);
  }, []);

  return (
    <div className="form-group" ref={wrapRef}>
      <label className="form-label">{label}</label>
      <input
        className={`form-input${showError && invalid ? " has-error" : ""}`}
        value={value.label}
        placeholder={`Search ${label.toLowerCase()} in Bengaluru…`}
        autoComplete="off"
        onChange={(e) => {
          const v = e.target.value;
          onSearch(v);
          onChange({ label: v, lat: "", lng: "" });
          setOpen(true);
        }}
        onFocus={() => {
          if (value.label) onSearch(value.label);
          setOpen(true);
        }}
      />
      {value.lat !== "" && value.lng !== "" && (
        <span className="coord-tag">
          {Number(value.lat).toFixed(4)}, {Number(value.lng).toFixed(4)}
        </span>
      )}
      {open && filtered.length > 0 && (
        <ul className="autocomplete-list">
          {filtered.map((s) => (
            <li
              key={`${s.name}-${s.lat}`}
              onMouseDown={(e) => {
                e.preventDefault();
                onChange({ label: s.name, lat: s.lat, lng: s.lng });
                setOpen(false);
              }}
            >
              {s.name}
            </li>
          ))}
        </ul>
      )}
      {showError && invalid && (
        <small className="field-error">
          Select a location from the list, or try a different Bengaluru area name.
        </small>
      )}
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
  originSuggestions,
  destinationSuggestions,
  onOriginSearch,
  onDestinationSearch,
  submitAttempted,
}) {
  return (
    <div className="card">
      <p className="section-label">Trip planner</p>
      <LocationInput
        label="Origin"
        value={origin}
        onChange={onOriginChange}
        suggestions={originSuggestions}
        onSearch={onOriginSearch}
        showError={submitAttempted}
      />
      <LocationInput
        label="Destination"
        value={destination}
        onChange={onDestinationChange}
        suggestions={destinationSuggestions}
        onSearch={onDestinationSearch}
        showError={submitAttempted}
      />
      <div className="form-row">
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Optimize for</label>
          <select
            className="form-select"
            value={optimizeFor}
            onChange={(e) => onOptimizeChange(e.target.value)}
          >
            <option value="time">Fastest</option>
            <option value="distance">Shortest</option>
            <option value="eco">Greenest</option>
          </select>
        </div>
        <div className="form-group" style={{ marginBottom: 0 }}>
          <label className="form-label">Vehicle</label>
          <select
            className="form-select"
            value={vehicleType}
            onChange={(e) => onVehicleChange(e.target.value)}
          >
            <option value="car">Car</option>
            <option value="bike">Bike</option>
            <option value="truck">Truck</option>
          </select>
        </div>
      </div>
      <button type="button" className="submit-btn" onClick={onSubmit} disabled={loading}>
        {loading ? "Calculating…" : "Find best route"}
      </button>
    </div>
  );
}
