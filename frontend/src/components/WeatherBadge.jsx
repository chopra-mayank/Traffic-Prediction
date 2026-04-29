export default function WeatherBadge({ weather }) {
  if (!weather) return null;
  return (
    <div className="weather-badge">
      <strong>{weather.city}</strong>
      <span>{weather.condition}</span>
      <span>{weather.temperature}°C</span>
      <span>Rain {weather.precipitation} mm</span>
      <span>Wind {weather.wind_speed} m/s</span>
    </div>
  );
}
