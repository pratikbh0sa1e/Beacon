import React, { useState } from "react";
import { Outlet } from "react-router-dom";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { Toaster } from "../ui/sonner";
import { cn } from "../../lib/utils";

export const MainLayout = () => {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="h-screen bg-background flex flex-col overflow-hidden">
      <Header onMenuClick={() => setSidebarOpen(!sidebarOpen)} />
      {/* <div className="flex"> */}
      <div className="flex flex-1 overflow-hidden">
        <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        {/* <main className="flex-1 min-w-0 transition-all duration-300 ease-in-out"> */}
        <main
          className={cn(
            "flex-1 overflow-y-auto bg-background/50 min-w-0 transition-all duration-300 ease-in-out",
            // ✅ FIX: Push content right when sidebar is open on Desktop
            sidebarOpen ? "lg:ml-64" : "lg:ml-0"
          )}
        >
          <div className="container max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <Outlet />
          </div>
        </main>
      </div>
      {/* <Toaster position="top-right" richColors /> */}
    </div>
  );
};
