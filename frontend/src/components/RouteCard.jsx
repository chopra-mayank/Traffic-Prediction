export default function RouteCard({ route, selected, onSelect }) {
  return (
    <button
      type="button"
      className={`route-card ${selected ? "selected" : ""}`}
      onClick={onSelect}
    >
      <div className="route-card-header">
        <strong>{route.label}</strong>
        {route.recommended ? <span className="pill pill-primary">Best</span> : null}
        {route.eco_badge ? <span className="pill pill-eco">Eco</span> : null}
      </div>
      <div className="route-grid">
        <span>⏱ {route.travel_time_min} min</span>
        <span>📏 {route.distance_km} km</span>
        <span>🌿 {route.co2_grams} g</span>
        <span>Traffic: {route.congestion_level}</span>
      </div>
    </button>
  );
}
