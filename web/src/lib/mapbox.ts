export function getMapboxToken(): string | undefined {
  const token = process.env.NEXT_PUBLIC_MAPBOX_TOKEN?.trim();
  return token || undefined;
}
