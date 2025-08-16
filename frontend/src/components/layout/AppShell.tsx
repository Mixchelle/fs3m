"use client";

import Sidebar from "@/components/global/Sidebar";
import Header from "@/components/global/Header";

const SIDEBAR_W = 160; // px
const HEADER_H = 56;   // px

export default function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background text-foreground overflow-x-hidden">
      <Sidebar />
      <div className="min-h-screen transition-all" style={{ paddingLeft: SIDEBAR_W }}>
        <Header />
        <main className="p-4 md:p-6" style={{ paddingTop: HEADER_H }}>
          {children}
        </main>
      </div>
    </div>
  );
}
