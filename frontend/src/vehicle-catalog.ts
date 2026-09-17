export type VehicleDefinition = {
  id: string;
  label: string;
} & ({ available: true; assetPath: string; artifactVersion: string; meshHash: string; evidenceUrl: string }
  | { available: false; reason: string });

export const vehicleCatalog: readonly VehicleDefinition[] = [
  { id: 'concept-coupe', label: 'Concept coupe', available: true,
    assetPath: '/models/car-concept.glb', artifactVersion: 'khronos-car-concept-2024-zephyr-cabin-v4',
    meshHash: 'sha256:c272098089d78c5cd9fd9f24ff50ee8acf8d932c55f2d55fc10adb6c8998966b',
    evidenceUrl: 'https://github.com/KhronosGroup/glTF-Sample-Assets/tree/main/Models/CarConcept' },
  { id: 'sedan', label: 'Sedan', available: false, reason: 'Licensed asset and surface mapping pending' },
  { id: 'suv', label: 'SUV', available: false, reason: 'Licensed asset and surface mapping pending' },
];

export function requireVehicle(id: string): Extract<VehicleDefinition, { available: true }> {
  const definition = vehicleCatalog.find(vehicle => vehicle.id === id);
  if (!definition) throw new Error(`Unknown vehicle: ${id}`);
  if (!definition.available) throw new Error(`${definition.label} unavailable: ${definition.reason}`);
  return definition;
}
