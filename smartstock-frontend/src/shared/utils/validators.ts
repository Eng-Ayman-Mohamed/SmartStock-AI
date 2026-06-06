export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

export function isNonEmpty(value: string): boolean {
  return value.trim().length > 0;
}

export function isPositiveInteger(value: string): boolean {
  const n = Number(value);
  return Number.isInteger(n) && n > 0;
}

export function isValidSKU(sku: string): boolean {
  return /^[A-Za-z0-9]{2,5}-\d{4}-\d{3,5}$/.test(sku);
}
