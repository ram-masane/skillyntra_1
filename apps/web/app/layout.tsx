import "./globals.css";

export const metadata = {
  title: "Skillyntra | From Skills to Opportunities",
  description: "Industry intelligence, skill gaps, learning, validation.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return <html lang="en"><body>{children}</body></html>;
}
