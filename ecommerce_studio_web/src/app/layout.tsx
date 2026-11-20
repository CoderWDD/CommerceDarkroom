import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Ecommerce Studio - 商业级电商视觉工坊 (Pro v2.1)",
  description: "Next.js 14 + shadcn/ui + FastAPI 现代化电商 9 宫格视觉暗房工坊与非破坏性版本链",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="dark">
      <body className="min-h-screen bg-zinc-950 text-zinc-100 antialiased selection:bg-sky-500/30 selection:text-sky-200">
        {children}
        <Toaster theme="dark" position="bottom-right" richColors />
      </body>
    </html>
  );
}
