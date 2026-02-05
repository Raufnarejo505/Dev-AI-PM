import React from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Topbar from "./Topbar";

export default function Layout() {
    const [mobileNavOpen, setMobileNavOpen] = React.useState(false);
    const [sidebarCollapsed, setSidebarCollapsed] = React.useState(false);

    const closeMobileNav = React.useCallback(() => {
        setMobileNavOpen(false);
    }, []);

    const toggleSidebar = React.useCallback(() => {
        setSidebarCollapsed(prev => !prev);
    }, []);

    return (
        <div className="min-h-screen bg-[#FAFAFF] flex">
            <Sidebar 
                isOpen={mobileNavOpen} 
                onClose={closeMobileNav} 
                isCollapsed={sidebarCollapsed}
                onToggle={toggleSidebar}
            />

            {mobileNavOpen ? (
                <button
                    type="button"
                    aria-label="Navigation schließen"
                    onClick={closeMobileNav}
                    className="fixed inset-0 z-30 bg-slate-900/40 lg:hidden"
                />
            ) : null}

            <div className={`flex-1 ml-0 min-w-0 transition-all duration-300 ease-in-out ${sidebarCollapsed ? 'lg:ml-16' : 'lg:ml-64'}`}>
                <Topbar onMenuClick={() => setMobileNavOpen(true)} />
                <main className="p-4 sm:p-6">
                    <Outlet />
                </main>
            </div>
        </div>
    );
}

