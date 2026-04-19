import type { Metadata } from "next";
import Link from "next/link";

import "./globals.css";

export const metadata: Metadata = {
  title: "TFM PoC",
  description: "Consola web simple para operar la PoC del TFM.",
};

const links = [
  ["/", "Inicio"],
  ["/infraestructura", "Infraestructura"],
  ["/ingesta", "Ingesta"],
  ["/gobierno", "Gobierno"],
  ["/workflow", "Workflow"],
  ["/dcat", "DCAT"],
  ["/runtime", "Estado vivo"],
  ["/validacion", "Validación"],
  ["/shacl", "SHACL"],
  ["/artefactos", "Artefactos"],
  ["/jobs", "Ejecuciones"],
  ["/preparacion", "Preparación"],
];

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="es">
      <body>
        <div className="shell">
          <aside className="sidebar">
            <h1>TFM PoC<br />Consola operativa</h1>
            <nav aria-label="Navegación principal">
              {links.map(([href, label]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="content">{children}</main>
        </div>
      </body>
    </html>
  );
}
