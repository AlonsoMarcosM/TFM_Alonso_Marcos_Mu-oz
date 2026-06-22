import { describe, expect, it } from "vitest";

import { sanitizePublicText, sanitizePublicValue } from "./publicSanitization";

describe("sanitizePublicText", () => {
  it("oculta rutas locales del repositorio y del perfil de Windows", () => {
    const input =
      "file:///F:/DISCO%20DURO%20PORTABLE/INGENIERIA/MASTER/TFM/TFM_Alonso_Marcos_Mu-oz " +
      "C:\\Users\\usuario\\AppData\\Local";

    const sanitized = sanitizePublicText(input);

    expect(sanitized).not.toContain("DISCO%20DURO");
    expect(sanitized).not.toContain("Users\\usuario");
    expect(sanitized).toContain("C:/portfolio/TFM_Alonso_Marcos_Mu-oz");
    expect(sanitized).toContain("C:\\portfolio-user\\AppData\\Local");
  });

  it("sanea cadenas anidadas sin alterar otros valores", () => {
    const value = { paths: ["C:\\Users\\Alonso\\repo"], count: 1 };

    expect(sanitizePublicValue(value)).toEqual({
      paths: ["C:\\portfolio-user\\repo"],
      count: 1,
    });
  });
});
