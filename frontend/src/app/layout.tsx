  import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";


export const metadata = {
  title: "FS3M",
  description: "Security Maturity Platform",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const setThemeInit = `
    try {
      const saved = localStorage.getItem('theme');
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      const dark = saved ? saved === 'dark' : prefersDark;
      const root = document.documentElement;
      if (dark) root.classList.add('dark'); else root.classList.remove('dark');
    } catch {}
  `;
  return (
    <html lang="pt-br">
      <head>
        <script dangerouslySetInnerHTML={{ __html: setThemeInit }} />
      </head>
      <body>
        <AuthProvider>{children}</AuthProvider>
      </body>
    </html>
  );
}
