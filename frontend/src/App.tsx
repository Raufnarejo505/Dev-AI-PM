import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Layout from "./components/Layout";
import { DashboardSkeleton } from "./components/LoadingSkeleton";
import { OfflineIndicator } from "./components/OfflineIndicator";
import { BackendStatusBanner } from "./components/BackendStatusBanner";
import React, { Suspense } from "react";
import { useT } from "./i18n/I18nProvider";
import Dashboard from "./pages/Dashboard";
import Login from "./pages/Login";
import Register from "./pages/Register";
import MachinesPage from "./pages/Machines";
import SensorsPage from "./pages/Sensors";
import PredictionsPage from "./pages/Predictions";
import AlarmsPage from "./pages/Alarms";
import TicketsPage from "./pages/Tickets";
import ReportsPage from "./pages/Reports";
import AIServicePage from "./pages/AIService";
import MQTTStatusPage from "./pages/MQTTStatus";
import OPCUAWizard from "./pages/OPCUAWizard";
import SettingsPage from "./pages/Settings";
import NotificationsPage from "./pages/Notifications";
import WebhooksPage from "./pages/Webhooks";
import RolesPage from "./pages/Roles";

function ProtectedRoute({ children }: { children: JSX.Element }) {
    const { isAuthenticated, isLoading } = useAuth();
    const location = useLocation();
    const t = useT();
    
    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#010313] flex items-center justify-center">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-400 mb-4"></div>
                    <div className="text-lg text-slate-100 mb-2">{t("common.loading")}</div>
                    <div className="text-sm text-slate-400">{t("common.initializing")}</div>
                </div>
            </div>
        );
    }
    
    if (!isAuthenticated) {
        return <Navigate to="/login" replace state={{ from: location }} />;
    }
    
    // Route-level caching with Suspense for smooth transitions
    return (
        <Suspense fallback={<DashboardSkeleton />}>
            {children}
        </Suspense>
    );
}

function AppRoutes() {
    return (
        <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
                path="/"
                element={
                    <ProtectedRoute>
                        <Layout />
                    </ProtectedRoute>
                }
            >
                <Route index element={<Dashboard />} />
                <Route path="machines" element={<MachinesPage />} />
                <Route path="sensors" element={<SensorsPage />} />
                <Route path="predictions" element={<PredictionsPage />} />
                <Route path="alarms" element={<AlarmsPage />} />
                <Route path="tickets" element={<TicketsPage />} />
                <Route path="reports" element={<ReportsPage />} />
                <Route path="ai" element={<AIServicePage />} />
                <Route path="mqtt" element={<MQTTStatusPage />} />
                <Route path="opcua" element={<OPCUAWizard />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="notifications" element={<NotificationsPage />} />
                <Route path="webhooks" element={<WebhooksPage />} />
                <Route path="roles" element={<RolesPage />} />
            </Route>
        </Routes>
    );
}

export default function App() {
    return (
        <AuthProvider>
            <BrowserRouter>
                <BackendStatusBanner />
                <AppRoutes />
                <OfflineIndicator />
            </BrowserRouter>
        </AuthProvider>
    );
}
