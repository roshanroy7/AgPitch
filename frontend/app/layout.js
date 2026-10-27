import "./globals.css";

export const metadata = {
  title: "AgPitch",
  description: "Live, explainable and personalised football match insights from AI agents on Azure.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
