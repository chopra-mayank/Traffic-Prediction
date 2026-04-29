const weatherIcon = {
  Clear: "☀️",
  Clouds: "☁️",
  Rain: "🌧️",
  Drizzle: "🌦️",
  Thunderstorm: "⛈️",
  Snow: "❄️",
  Mist: "🌫️",
  Haze: "🌫️",
  Fog: "🌫️",
};

export default function WeatherBadge({ weather }) {
  if (!weather) return null;
  const icon = weatherIcon[weather.condition] || "🌤️";
  return (
    <div className="card">
      <p className="section-label">Current weather</p>
      <div className="weather-row">
        <span style={{ fontSize: "1.4rem" }}>{icon}</span>
        <span className="weather-city">{weather.city}</span>
        <span style={{ fontWeight: 700, fontSize: "0.95rem" }}>{weather.temperature}°C</span>
        <div className="weather-chips">
          <span className="weather-chip">{weather.condition}</span>
          <span className="weather-chip">Rain {weather.precipitation} mm</span>
          <span className="weather-chip">Wind {weather.wind_speed} m/s</span>
        </div>
      </div>
    </div>
  );
}
