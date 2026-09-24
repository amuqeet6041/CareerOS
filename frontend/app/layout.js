import "./globals.css";
import ThemeProvider from "@/components/shared/ThemeProvider";

export const metadata = {
  title: "CareerOS",
  description:
    "AI-powered career platform: resume analysis, job matching, and career insights.",
};

const THEME_INIT_SCRIPT = `(function(){try{var t=localStorage.getItem("careeros_theme");var dark=t?t==="dark":window.matchMedia&&window.matchMedia("(prefers-color-scheme: dark)").matches;if(dark){document.documentElement.classList.add("dark")}}catch(e){}})();`;

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-screen bg-canvas font-sans text-navy antialiased">
        <ThemeProvider>{children}</ThemeProvider>
      </body>
    </html>
  );
}