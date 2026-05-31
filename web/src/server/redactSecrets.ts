const SECRET_KEYS = [
  "OPENMETADATA_JWT_TOKEN",
  "GITHUB_TOKEN",
  "GH_TOKEN",
];

export function redactSecrets(value: string, env: Partial<NodeJS.ProcessEnv> = process.env): string {
  let out = value;
  for (const key of SECRET_KEYS) {
    const secret = env[key];
    if (!secret || secret.length < 4) {
      continue;
    }
    out = out.split(secret).join(`[${key}:redacted]`);
  }
  return out;
}
