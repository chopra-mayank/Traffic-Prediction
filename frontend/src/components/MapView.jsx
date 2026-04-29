import { useEffect } from "react";
import { MapContainer, Marker, Polyline, Popup, TileLayer, useMap } from "react-leaflet";

const fallbackCenter = [12.9716, 77.5946];

function congestionColor(level) {
  if (level === "low") return "#22c55e";
  if (level === "medium") return "#f59e0b";
  if (level === "high") return "#ef4444";
  return "#6366f1";
}

function isValid(v) {
  return typeof v === "number" && !Number.isNaN(v);
}

function ChangeView({ center }) {
  const map = useMap();
  useEffect(() => {
    if (center) {
      map.flyTo(center, map.getZoom(), { duration: 0.8 });
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [center?.[0], center?.[1]]);
  return null;
}

export default function MapView({ origin, destination, routes, selectedRouteIndex, onSelectRoute }) {
  const hasOrigin = isValid(origin.lat) && isValid(origin.lng);
  const hasDestination = isValid(destination.lat) && isValid(destination.lng);

  const center =
    hasOrigin && hasDestination
      ? [(origin.lat + destination.lat) / 2, (origin.lng + destination.lng) / 2]
      : fallbackCenter;

  const hasRoutes = routes?.length > 0;

  return (
    <div className="map-area">
      <MapContainer center={center} zoom={12} scrollWheelZoom className="map-canvas">
        <ChangeView center={hasRoutes ? center : null} />
        <TileLayer
          attribution="&copy; OpenStreetMap contributors"
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {hasOrigin && (
          <Marker position={[origin.lat, origin.lng]}>
            <Popup>{origin.label || "Origin"}</Popup>
          </Marker>
        )}
        {hasDestination && (
          <Marker position={[destination.lat, destination.lng]}>
            <Popup>{destination.label || "Destination"}</Popup>
          </Marker>
        )}
        {/* draw unselected routes first so selected renders on top */}
        {routes?.map((route, index) => {
          if (index === selectedRouteIndex) return null;
          return (
            <Polyline
              key={route.route_index}
              positions={route.coordinates}
              color={congestionColor(route.congestion_level)}
              opacity={0.45}
              weight={4}
              eventHandlers={{ click: () => onSelectRoute(index) }}
            />
          );
        })}
        {/* selected route on top */}
        {hasRoutes && routes[selectedRouteIndex] && (
          <Polyline
            key={`selected-${selectedRouteIndex}`}
            positions={routes[selectedRouteIndex].coordinates}
            color={congestionColor(routes[selectedRouteIndex].congestion_level)}
            opacity={1}
            weight={7}
          />
        )}
      </MapContainer>

      {hasRoutes && (
        <div className="map-legend">
          <span className="legend-label">Traffic</span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#22c55e" }} />
            Low
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#f59e0b" }} />
            Medium
          </span>
          <span className="legend-item">
            <span className="legend-dot" style={{ background: "#ef4444" }} />
            High
          </span>
        </div>
      )}
    </div>
  );
}
