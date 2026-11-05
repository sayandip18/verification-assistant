import type { Metadata } from "next";
import { AppChrome } from "@/components/AppChrome";
import { AuthProvider } from "@/lib/auth";
import "./globals.css";

export const metadata: Metadata = {
  title: "BLLRO Mutation Assistant",
  description: "Workflow management for land mutation and verification officers",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <AuthProvider>
          <AppChrome>{children}</AppChrome>
        </AuthProvider>
      </body>
    </html>
  );
}
