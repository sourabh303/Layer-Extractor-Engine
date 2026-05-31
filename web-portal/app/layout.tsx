import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'Web Portal',
  description: 'Supabase-powered web portal for authentication and billing',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
