import path from "node:path";

import { isDemoMode } from "./demo";

export function repoRoot(): string {
  if (process.env.TFM_REPO_ROOT) {
    return path.resolve(process.env.TFM_REPO_ROOT);
  }
  // En modo demo todas las lecturas (`repoPath(...)`) se resuelven contra los
  // fixtures congelados de `web/demo/`, que reproducen la estructura del repo.
  if (isDemoMode()) {
    return path.resolve(process.cwd(), "demo");
  }
  return path.resolve(process.cwd(), "..");
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
