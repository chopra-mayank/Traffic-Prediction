export default function RouteCard({ route, selected, onSelect }) {
  const cong = route.congestion_level || "unknown";
  return (
    <button
      type="button"
      className={`route-card cong-${cong}${selected ? " selected" : ""}`}
      onClick={onSelect}
    >
      <div className="route-header">
        <span className="route-name">{route.label}</span>
        {route.recommended && <span className="pill pill-best">Best</span>}
        {route.eco_badge && <span className="pill pill-eco">Eco</span>}
        <span className={`pill pill-${cong}`}>{cong}</span>
      </div>
      <div className="route-stats">
        <span className="route-stat">⏱ {route.travel_time_min} min</span>
        <span className="route-stat">📏 {route.distance_km} km</span>
        <span className="route-stat">🌿 {route.co2_grams} g CO₂</span>
        <span className="route-stat">🚦 {cong} traffic</span>
      </div>
    </button>
  );
}
