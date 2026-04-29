import { MapContainer, Marker, Polyline, Popup, TileLayer } from "react-leaflet";

const colorScale = ["#1fb36a", "#ffb703", "#f25f5c"];
const fallbackCenter = [12.9716, 77.5946];

function isValidCoordinate(value) {
  return typeof value === "number" && !Number.isNaN(value);
}

export default function MapView({ origin, destination, routes, selectedRouteIndex }) {
  const selected = routes?.[selectedRouteIndex];
  const hasOrigin = isValidCoordinate(origin.lat) && isValidCoordinate(origin.lng);
  const hasDestination = isValidCoordinate(destination.lat) && isValidCoordinate(destination.lng);
  const center = hasOrigin && hasDestination
    ? [
        (origin.lat + destination.lat) / 2,
        (origin.lng + destination.lng) / 2,
      ]
    : fallbackCenter;

  return (
    <section className="map-shell glass">
      <MapContainer center={center} zoom={12} scrollWheelZoom className="map-canvas">
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {hasOrigin ? (
          <Marker position={[origin.lat, origin.lng]}>
            <Popup>{origin.label || "Origin"}</Popup>
          </Marker>
        ) : null}
        {hasDestination ? (
          <Marker position={[destination.lat, destination.lng]}>
            <Popup>{destination.label || "Destination"}</Popup>
          </Marker>
        ) : null}
        {routes?.map((route, index) => (
          <Polyline
            key={route.route_index}
            positions={route.coordinates}
            color={index === selectedRouteIndex ? "#0f172a" : colorScale[index % colorScale.length]}
            opacity={index === selectedRouteIndex ? 0.95 : 0.6}
            weight={index === selectedRouteIndex ? 6 : 4}
          />
        ))}
      </MapContainer>
      {selected ? (
        <div className="legend">
          <span className="legend-title">Traffic legend</span>
          <span><i style={{ background: "#1fb36a" }} /> Low</span>
          <span><i style={{ background: "#ffb703" }} /> Medium</span>
          <span><i style={{ background: "#f25f5c" }} /> High</span>
        </div>
      ) : null}
    </section>
  );
}
