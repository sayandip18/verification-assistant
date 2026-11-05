export function mergeExtracted<T extends Record<string, unknown>>(current: T, extracted: Partial<T> | Record<string, unknown>): T {
  const next = { ...current };
  for (const [key, value] of Object.entries(extracted)) {
    if (value === null || value === undefined || value === "") continue;
    const existing = next[key as keyof T];
    if (existing === "" || existing === 0 || existing === null || existing === undefined) {
      (next as Record<string, unknown>)[key] = value;
    }
  }
  return next;
}
