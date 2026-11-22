import type { Metadata } from "next";
import "./globals.css";
import { Toaster } from "sonner";

export const metadata: Metadata = {
  title: "Ecommerce Studio - 商业级电商视觉工坊 (Pro v2.1)",
  description: "Next.js 14 + shadcn/ui + FastAPI 现代化电商 9 宫格视觉商业工坊与非破坏性版本链",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body className="min-h-screen bg-background text-foreground antialiased selection:bg-blue-500/20 selection:text-blue-700">
        {children}
        <Toaster theme="light" position="bottom-right" richColors />
      </body>
    </html>
  );
}
