const PUBLIC_REPO_PATH = "C:\\portfolio\\TFM_Alonso_Marcos_Mu-oz";

export function sanitizePublicText(value: string): string {
  return value
    .replace(
      /file:\/\/\/[A-Za-z]:\/DISCO%20DURO%20PORTABLE\/INGENIERIA\/MASTER\/TFM\/TFM_Alonso_Marcos_Mu-oz/gi,
      `file:///${PUBLIC_REPO_PATH.replaceAll("\\", "/")}`,
    )
    .replace(
      /[A-Za-z]:[\\/]DISCO DURO PORTABLE[\\/]INGENIERIA[\\/]MASTER[\\/]TFM[\\/]TFM_Alonso_Marcos_Mu-oz/gi,
      PUBLIC_REPO_PATH,
    )
    .replace(/[A-Za-z]:[\\/]Users[\\/][^\\/\s"'<>]+/gi, "C:\\portfolio-user")
    .replace(/\b[A-Za-z]:\\(?!portfolio(?:-user)?\\)/gi, "C:\\portfolio\\")
    .replace(/\b[A-Za-z]:\/(?!portfolio\/)/gi, "C:/portfolio/");
}

export function sanitizePublicValue<T>(value: T): T {
  if (typeof value === "string") {
    return sanitizePublicText(value) as T;
  }
  if (Array.isArray(value)) {
    return value.map((item) => sanitizePublicValue(item)) as T;
  }
  if (value && typeof value === "object") {
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, sanitizePublicValue(item)]),
    ) as T;
  }
  return value;
}
