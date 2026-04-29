import fsp from "node:fs/promises";

import { repoPath } from "./repoPaths";

export const editableConfigFiles = [
  {
    id: "governance_defaults.yaml",
    title: "Defaults DCAT/HVD",
    description: "Catálogo, publicador, licencias, HVD, contacto y URLs base derivadas.",
  },
  {
    id: "mapping_rules.yaml",
    title: "Reglas de mapeo",
    description: "Capa publicable, dominios por esquema y tags por prefijo de tabla.",
  },
  {
    id: "operational_profile.yaml",
    title: "Perfil operativo",
    description: "Rutas canónicas, perfil SHACL activo, warnings y refresco de hoja.",
  },
] as const;

export type EditableConfigId = (typeof editableConfigFiles)[number]["id"];

export function findEditableConfig(id: string) {
  return editableConfigFiles.find((file) => file.id === id);
}

export function editableConfigPath(id: string): string {
  const file = findEditableConfig(id);
  if (!file) {
    throw new Error(`Configuracion no editable: ${id}`);
  }
  return repoPath("tfm_ingestor", "config", file.id);
}

export async function readEditableConfig(id: string): Promise<string> {
  return fsp.readFile(editableConfigPath(id), "utf8");
}

export async function writeEditableConfig(id: string, content: string): Promise<void> {
  if (content.trim().length === 0) {
    throw new Error("El contenido no puede quedar vacio.");
  }
  await fsp.writeFile(editableConfigPath(id), content, "utf8");
}
