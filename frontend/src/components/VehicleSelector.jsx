export default function VehicleSelector({ value, onChange }) {
  return (
    <label className="field">
      <span>Vehicle type</span>
      <select value={value} onChange={(event) => onChange(event.target.value)}>
        <option value="car">Car</option>
        <option value="bike">Bike</option>
        <option value="truck">Truck</option>
      </select>
    </label>
  );
}
