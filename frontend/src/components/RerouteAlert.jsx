export default function RerouteAlert({ message, onAccept, onDismiss }) {
  if (!message) return null;
  return (
    <div className="reroute-toast">
      <h4>Faster route available</h4>
      <p>{message}</p>
      <div className="reroute-actions">
        <button type="button" onClick={onAccept}>Switch route</button>
        <button type="button" className="ghost" onClick={onDismiss}>Keep current</button>
      </div>
    </div>
  );
}
