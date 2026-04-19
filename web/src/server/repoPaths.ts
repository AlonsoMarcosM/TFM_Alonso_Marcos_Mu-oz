import path from "node:path";

export function repoRoot(): string {
  return process.env.TFM_REPO_ROOT
    ? path.resolve(process.env.TFM_REPO_ROOT)
    : path.resolve(process.cwd(), "..");
}

export function repoPath(...parts: string[]): string {
  return path.join(repoRoot(), ...parts);
}

export function relativeToRepo(absolutePath: string): string {
  return path.relative(repoRoot(), absolutePath).replaceAll(path.sep, "/");
}

export function assertInsideRepo(absolutePath: string): string {
  const resolved = path.resolve(absolutePath);
  const root = repoRoot();
  if (resolved !== root && !resolved.startsWith(root + path.sep)) {
    throw new Error(`Path is outside repo root: ${resolved}`);
  }
  return resolved;
}
