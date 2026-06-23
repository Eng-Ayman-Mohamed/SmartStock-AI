export function getApiBaseUrl(): string {
  const envCfg = (window as unknown as Record<string, unknown>)['__ENV__'] as Record<string, string> | undefined;
  return (
    envCfg?.VITE_API_BASE_URL ||
    import.meta.env.VITE_API_BASE_URL ||
    envCfg?.VITE_API_URL ||
    import.meta.env.VITE_API_URL ||
    '/api'
  );
}
