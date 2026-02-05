import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n/I18nProvider";

type IconName =
    | "home"
    | "dashboard"
    | "machines"
    | "sensors"
    | "predictions"
    | "alarms"
    | "tickets"
    | "reports"
    | "ai"
    | "opcua"
    | "settings"
    | "notifications"
    | "webhooks"
    | "roles";

interface NavItem {
    label: string;
    path?: string;
    icon: IconName;
    requireRole?: string[];
    children?: NavItem[];
}

interface NavSection {
    title?: string;
    items: NavItem[];
}

type SidebarProps = {
    isOpen?: boolean;
    onClose?: () => void;
    isCollapsed?: boolean;
    onToggle?: () => void;
};

function NavIcon({ name, active }: { name: IconName; active: boolean }) {
    const common = "w-5 h-5";
    const stroke = active ? "#6D28D9" : "#8B5CF6";

    const Svg = ({ children }: { children: React.ReactNode }) => (
        <svg
            viewBox="0 0 24 24"
            className={common}
            fill="none"
            stroke={stroke}
            strokeWidth="1.8"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
        >
            {children}
        </svg>
    );

    switch (name) {
        case "home":
            return (
                <Svg>
                    <path d="M3 10.5 12 3l9 7.5" />
                    <path d="M5 9.5V21h14V9.5" />
                </Svg>
            );
        case "dashboard":
            return (
                <Svg>
                    <path d="M4 13V6a2 2 0 0 1 2-2h4v9H4z" />
                    <path d="M14 20v-7h6v5a2 2 0 0 1-2 2h-4z" />
                    <path d="M14 4h4a2 2 0 0 1 2 2v4h-6V4z" />
                    <path d="M4 17h6v3H6a2 2 0 0 1-2-2v-1z" />
                </Svg>
            );
        case "machines":
            return (
                <Svg>
                    <rect x="4" y="6" width="16" height="10" rx="2" />
                    <path d="M7 20h10" />
                    <path d="M8 10h8" />
                </Svg>
            );
        case "sensors":
            return (
                <Svg>
                    <path d="M12 20a8 8 0 1 0-8-8" />
                    <path d="M12 16a4 4 0 1 0-4-4" />
                    <path d="M12 12h.01" />
                </Svg>
            );
        case "predictions":
            return (
                <Svg>
                    <path d="M4 19V5" />
                    <path d="M4 19h16" />
                    <path d="M7 15l3-3 3 2 5-6" />
                </Svg>
            );
        case "alarms":
            return (
                <Svg>
                    <path d="M18 8a6 6 0 1 0-12 0c0 7-2 7-2 7h16s-2 0-2-7" />
                    <path d="M9.5 19a2.5 2.5 0 0 0 5 0" />
                </Svg>
            );
        case "tickets":
            return (
                <Svg>
                    <path d="M4 9a2 2 0 0 1 2-2h12a2 2 0 0 1 2 2" />
                    <path d="M6 7v10a2 2 0 0 0 2 2h8a2 2 0 0 0 2-2V7" />
                    <path d="M9 11h6" />
                    <path d="M9 15h4" />
                </Svg>
            );
        case "reports":
            return (
                <Svg>
                    <rect x="6" y="4" width="12" height="16" rx="2" />
                    <path d="M9 9h6" />
                    <path d="M9 13h6" />
                    <path d="M9 17h4" />
                </Svg>
            );
        case "ai":
            return (
                <Svg>
                    <path d="M12 3c4 0 8 3 8 7 0 2-1 3-2 4" />
                    <path d="M12 3c-4 0-8 3-8 7 0 3 2 5 5 6" />
                    <path d="M10 21h4" />
                    <path d="M8 14h8" />
                    <path d="M9 10h.01" />
                    <path d="M15 10h.01" />
                </Svg>
            );
        case "opcua":
            return (
                <Svg>
                    <rect x="6" y="4" width="12" height="16" rx="2" />
                    <path d="M9 8h6" />
                    <path d="M9 12h6" />
                    <path d="M9 16h4" />
                </Svg>
            );
        case "settings":
            return (
                <Svg>
                    <path d="M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z" />
                    <path d="M19.4 15a1.8 1.8 0 0 0 .4 2l-1.2 2.1a2 2 0 0 1-2.3.9l-1.6-.6a8.2 8.2 0 0 1-1.7 1l-.2 1.7a2 2 0 0 1-2 1.8h-2.4a2 2 0 0 1-2-1.8l-.2-1.7a8.2 8.2 0 0 1-1.7-1l-1.6.6a2 2 0 0 1-2.3-.9L4.2 17a1.8 1.8 0 0 0 .4-2 8 8 0 0 1 0-2l-.4-2 1.2-2.1a2 2 0 0 1 2.3-.9l1.6.6a8.2 8.2 0 0 1 1.7-1l.2-1.7a2 2 0 0 1 2-1.8h2.4a2 2 0 0 1 2 1.8l.2 1.7a8.2 8.2 0 0 1 1.7 1l1.6-.6a2 2 0 0 1 2.3.9l1.2 2.1-.4 2a8 8 0 0 1 0 2z" />
                </Svg>
            );
        case "notifications":
            return (
                <Svg>
                    <path d="M18 8a6 6 0 1 0-12 0c0 7-2 7-2 7h16s-2 0-2-7" />
                    <path d="M9.5 19a2.5 2.5 0 0 0 5 0" />
                </Svg>
            );
        case "webhooks":
            return (
                <Svg>
                    <path d="M10 13a4 4 0 0 1 0-8h3" />
                    <path d="M14 11a4 4 0 0 1 0 8h-3" />
                    <path d="M8.5 10.5 15.5 13.5" />
                </Svg>
            );
        case "roles":
            return (
                <Svg>
                    <path d="M16 11a4 4 0 1 0-8 0" />
                    <path d="M4 21a8 8 0 0 1 16 0" />
                </Svg>
            );
        default:
            return null;
    }
}

const navSections: NavSection[] = [
    {
        items: [
            { path: "/", label: "Dashboard", icon: "dashboard" },
            { path: "/machines", label: "Machines", icon: "machines" },
            { path: "/sensors", label: "Sensors", icon: "sensors" },
            { path: "/predictions", label: "Predictions", icon: "predictions" },
            { path: "/alarms", label: "Alarms", icon: "alarms" },
            { path: "/tickets", label: "Tickets", icon: "tickets" },
            { path: "/reports", label: "Reports", icon: "reports" },
        ],
    },
    {
        title: "AI & Integration",
        items: [
            { path: "/ai", label: "AI Service", icon: "ai", requireRole: ["engineer", "admin"] },
            { path: "/opcua", label: "OPC UA Wizard", icon: "opcua", requireRole: ["engineer", "admin"] },
        ],
    },
    {
        items: [
            {
                path: "/settings",
                label: "Settings",
                icon: "settings",
                requireRole: ["engineer", "admin"],
                children: [
                    { path: "/notifications", label: "Notifications", icon: "notifications", requireRole: ["engineer", "admin"] },
                    { path: "/webhooks", label: "Webhooks", icon: "webhooks", requireRole: ["engineer", "admin"] },
                    { path: "/roles", label: "Roles", icon: "roles", requireRole: ["admin"] },
                ],
            },
        ],
    },
];

export default function Sidebar({ isOpen = false, onClose, isCollapsed = false, onToggle }: SidebarProps) {
    const location = useLocation();
    const { user } = useAuth();
    const t = useT();

    const canAccess = (item: NavItem): boolean => {
        if (!item.requireRole) return true;
        if (!user?.role) return false;
        return item.requireRole.includes(user.role.toLowerCase());
    };

    const isPathActive = (path?: string) => {
        if (!path) return false;
        if (path === "/") return location.pathname === "/";
        return location.pathname.startsWith(path);
    };

    const canAccessItem = (item: NavItem): boolean => {
        if (!canAccess(item)) return false;
        if (item.children && item.children.length > 0) {
            return item.children.some(canAccessItem) || !!item.path;
        }
        return true;
    };

    const sections: NavSection[] = React.useMemo(
        () => [
            {
                items: [
                    { path: "/", label: t("nav.dashboard"), icon: "dashboard" },
                    { path: "/machines", label: t("nav.machines"), icon: "machines" },
                    { path: "/sensors", label: t("nav.sensors"), icon: "sensors" },
                    { path: "/predictions", label: t("nav.predictions"), icon: "predictions" },
                    { path: "/alarms", label: t("nav.alarms"), icon: "alarms" },
                    { path: "/tickets", label: t("nav.tickets"), icon: "tickets" },
                    { path: "/reports", label: t("nav.reports"), icon: "reports" },
                ],
            },
            {
                title: t("nav.aiIntegration"),
                items: [
                    { path: "/ai", label: t("nav.aiService"), icon: "ai", requireRole: ["engineer", "admin"] },
                    { path: "/opcua", label: t("nav.opcuaWizard"), icon: "opcua", requireRole: ["engineer", "admin"] },
                ],
            },
            {
                items: [
                    {
                        path: "/settings",
                        label: t("nav.settings"),
                        icon: "settings",
                        requireRole: ["engineer", "admin"],
                        children: [
                            { path: "/notifications", label: t("nav.notifications"), icon: "notifications", requireRole: ["engineer", "admin"] },
                            { path: "/webhooks", label: t("nav.webhooks"), icon: "webhooks", requireRole: ["engineer", "admin"] },
                            { path: "/roles", label: t("nav.roles"), icon: "roles", requireRole: ["admin"] },
                        ],
                    },
                ],
            },
        ],
        [t]
    );

    const filteredSections: NavSection[] = sections
        .map((section) => ({
            ...section,
            items: section.items.filter(canAccessItem),
        }))
        .filter((section) => section.items.length > 0);

    const renderNavItem = (item: NavItem, depth: number) => {
        const active = isPathActive(item.path) || (item.children ? item.children.some((c) => isPathActive(c.path)) : false);
        const base = depth === 0 ? "px-4 py-2.5" : "px-4 py-2";
        const text = depth === 0 ? "text-[15px]" : "text-[13px]";
        const indent = depth === 0 ? "" : "pl-11";
        const collapsedBase = isCollapsed ? "px-2 py-2.5 justify-center" : base;
        const collapsedIndent = isCollapsed ? "" : indent;

        const className = `group flex items-center ${collapsedBase} ${collapsedIndent} rounded-xl transition-colors overflow-hidden ${
            active
                ? "bg-gradient-to-r from-purple-100/80 to-purple-50 text-[#4C1D95]"
                : "text-[#4B5563] hover:bg-purple-50/70 hover:text-[#1F2937]"
        }`;

        const content = (
            <>
                <div className="flex items-center justify-center w-6 flex-shrink-0">
                    <NavIcon name={item.icon} active={active} />
                </div>
                {!isCollapsed && (
                    <span className={`font-medium ${text} whitespace-nowrap overflow-hidden text-ellipsis`}>{item.label}</span>
                )}
            </>
        );

        return (
            <div key={item.path || item.label} className="space-y-1">
                {item.path ? (
                    <Link
                        to={item.path}
                        className={className}
                        onClick={() => {
                            if (onClose) onClose();
                        }}
                    >
                        {content}
                    </Link>
                ) : (
                    <div className={className}>{content}</div>
                )}
                {item.children && item.children.length > 0 ? (
                    <div className="space-y-1">
                        {item.children.filter(canAccessItem).map((child) => renderNavItem(child, depth + 1))}
                    </div>
                ) : null}
            </div>
        );
    };

    return (
        <aside
            className={`fixed left-0 top-0 h-full z-40 overflow-hidden transition-all duration-300 ease-in-out
                ${isCollapsed ? "w-16" : "w-64"}
                ${isOpen ? "translate-x-0" : "-translate-x-full"}
                lg:translate-x-0`}
        >
            <div className={`${isCollapsed ? "p-2" : "p-6"} h-full overflow-y-auto`}>
                <div className="rounded-[28px] bg-white/80 border border-purple-100 shadow-[0_12px_40px_rgba(139,92,246,0.12)] backdrop-blur px-4 py-5">
                    {/* Toggle Button */}
                    <div className="flex justify-center mb-4">
                        <button
                            type="button"
                            aria-label={isCollapsed ? "Sidebar erweitern" : "Sidebar einklappen"}
                            onClick={onToggle}
                            className="hidden lg:flex items-center justify-center w-8 h-8 rounded-lg border border-slate-200 bg-white hover:bg-purple-50 transition-colors flex-shrink-0"
                        >
                            <svg className="w-4 h-4 text-slate-700" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                                {isCollapsed ? (
                                    <path d="M9 18l6-6-6-6" />
                                ) : (
                                    <path d="M15 18l-6-6 6-6" />
                                )}
                            </svg>
                        </button>
                    </div>

                    <nav className={`${isCollapsed ? 'space-y-2' : 'space-y-4'}`}>
                        {filteredSections.map((section, idx) => (
                            <div key={section.title || idx} className="space-y-2">
                                {!isCollapsed && section.title ? (
                                    <>
                                        <div className="h-px bg-slate-200/70 my-2" />
                                        <div className="px-3 pt-2 text-xs font-semibold tracking-wide text-[#9CA3AF] truncate">
                                            {section.title}
                                        </div>
                                    </>
                                ) : !isCollapsed && idx !== 0 ? (
                                    <div className="h-px bg-slate-200/70 my-2" />
                                ) : null}

                                <div className="space-y-1">
                                    {section.items.map((item) => renderNavItem(item, 0))}
                                </div>
                            </div>
                        ))}
                    </nav>
                </div>
            </div>
        </aside>
    );
}

