import type { Metadata } from "next";
import Link from "next/link";

import { isDemoMode } from "@/server/demo";

import "./globals.css";

export const metadata: Metadata = {
  title: "Plataforma de Gobierno del Dato",
  description: "Consola web operativa de la Plataforma de Gobierno del Dato del TFM.",
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
            <div className="brand">
              <svg
                className="brand-logo"
                viewBox="0 0 64 64"
                role="img"
                aria-label="Logotipo de la Plataforma de Gobierno del Dato"
              >
                <defs>
                  <linearGradient id="brand-gpgd" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0" stopColor="#1d7f5f" />
                    <stop offset="1" stopColor="#116046" />
                  </linearGradient>
                </defs>
                <rect width="64" height="64" rx="14" fill="url(#brand-gpgd)" />
                <g stroke="#ffffff" strokeWidth="3.2" strokeLinecap="round" fill="#ffffff">
                  <line x1="32" y1="22" x2="19" y2="44" />
                  <line x1="32" y1="22" x2="45" y2="44" />
                  <line x1="19" y1="44" x2="45" y2="44" />
                  <circle cx="32" cy="22" r="6.4" />
                  <circle cx="19" cy="44" r="6.4" />
                  <circle cx="45" cy="44" r="6.4" />
                </g>
              </svg>
              <h1>Plataforma de Gobierno del Dato<br />Consola operativa</h1>
            </div>
            <nav aria-label="Navegación principal">
              {links.map(([href, label]) => (
                <Link key={href} href={href}>
                  {label}
                </Link>
              ))}
            </nav>
          </aside>
          <main className="content">
            {isDemoMode() ? (
              <div className="demo-banner" role="status">
                <strong>Demo en solo lectura.</strong> Datos congelados de una ejecución real del
                caso de uso. La ejecución contra OpenMetadata y Kubernetes está deshabilitada; los
                botones muestran los artefactos reproducidos, no lanzan procesos.
              </div>
            ) : null}
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
