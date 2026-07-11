import type { Metadata } from "next";
import { Montserrat, Cormorant_Garamond, Italiana } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { BookingProvider } from "@/hooks/useBookingState";
import SchemaOrg from "@/components/seo/SchemaOrg";

const montserrat = Montserrat({ 
  subsets: ["latin"],
  variable: '--font-montserrat',
  display: 'swap',
});

const cormorant = Cormorant_Garamond({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: '--font-cormorant',
  display: 'swap',
});

const italiana = Italiana({
  subsets: ["latin"],
  weight: "400",
  variable: '--font-italiana',
  display: 'swap',
});

export const metadata: Metadata = {
  title: {
    default: 'Le Vagas - Luxury Hill Resort in Vagamon',
    template: '%s | Le Vagas'
  },
  description: 'Boutique hill retreat in Vagamon, Kerala. Experience serenity, nature, and luxury in our private cottages.',
  metadataBase: new URL('https://levagas.com'),
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`${montserrat.variable} ${cormorant.variable} ${italiana.variable} scroll-smooth`}>
      <body className="antialiased flex flex-col min-h-screen">
        <SchemaOrg />
        <BookingProvider>
          <Header />
          <main className="flex-grow">{children}</main>
          <Footer />
        </BookingProvider>
      </body>
    </html>
  );
}
