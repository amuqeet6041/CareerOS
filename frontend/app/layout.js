import "./globals.css";

export const metadata = {
  title: "CareerOS",
  description: "AI-powered career platform: resume analysis, job matching, and career insights.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-surface text-navy antialiased">
        {children}
      </body>
    </html>
  );
}
