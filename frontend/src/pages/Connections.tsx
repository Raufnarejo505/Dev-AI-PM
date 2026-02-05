import React, { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { connectionsApi, MSSQLConfig } from "../api/connections";
import { useErrorToast } from "../components/ErrorToast";
import { CardSkeleton } from "../components/LoadingSkeleton";
import { useT } from "../i18n/I18nProvider";

function normalizePassword(value: string) {
    if (!value) return "";
    if (value === "********") return "";
    return value;
}

export default function ConnectionsPage() {
    const t = useT();
    const { showError, ErrorComponent } = useErrorToast();
    const queryClient = useQueryClient();

    const { data, isLoading } = useQuery({
        queryKey: ["connections"],
        queryFn: () => connectionsApi.get(),
        refetchInterval: 60000,
    });

    const initial = useMemo(() => {
        return data?.mssql;
    }, [data]);

    const [mssql, setMssql] = useState<MSSQLConfig>({
        enabled: false,
        host: "",
        port: 1433,
        username: "",
        password: "",
        database: "HISTORISCH",
        table: "Tab_Actual",
        poll_interval_seconds: 60,
        window_minutes: 10,
        max_rows_per_poll: 5000,
    });

    useEffect(() => {
        if (!initial) return;
        setMssql({
            ...initial,
            password: normalizePassword((initial as any).password || ""),
        });
    }, [initial]);

    const saveMutation = useMutation({
        mutationFn: () =>
            connectionsApi.update({
                mssql: {
                    ...mssql,
                    password: mssql.password ? String(mssql.password) : "",
                },
            }),
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ["connections"] });
            showError(t("connections.toast.saved"));
        },
        onError: (error: any) => {
            showError(
                `${t("connections.toast.saveFailed")} ${error.response?.data?.detail || error.message}`
            );
        },
    });

    const testMutation = useMutation({
        mutationFn: () => {
            const pwd = String(mssql.password || "").trim();
            if (!pwd) {
                return connectionsApi.testMssql();
            }
            return connectionsApi.testMssql({ config: { ...mssql, password: pwd } });
        },
        onSuccess: (res) => {
            if (res.ok) {
                showError(t("connections.toast.testOk"));
            } else {
                showError(`${t("connections.toast.testFailed")} ${res.message}`);
            }
        },
        onError: (error: any) => {
            showError(
                `${t("connections.toast.testFailed")} ${error.response?.data?.detail || error.message}`
            );
        },
    });

    if (isLoading) {
        return <CardSkeleton />;
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-100">{t("connections.title")}</h1>
                <p className="text-slate-400 mt-1">{t("connections.subtitle")}</p>
            </div>

            <div className="bg-slate-900/70 border border-slate-700/40 rounded-2xl p-6">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.enabled")}</div>
                        <select
                            value={mssql.enabled ? "true" : "false"}
                            onChange={(e) => setMssql({ ...mssql, enabled: e.target.value === "true" })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        >
                            <option value="false">{t("connections.common.disabled")}</option>
                            <option value="true">{t("connections.common.enabled")}</option>
                        </select>
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.host")}</div>
                        <input
                            value={mssql.host}
                            onChange={(e) => setMssql({ ...mssql, host: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                            placeholder="10.1.61.252"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.port")}</div>
                        <input
                            type="number"
                            value={mssql.port}
                            onChange={(e) => setMssql({ ...mssql, port: Number(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.username")}</div>
                        <input
                            value={mssql.username}
                            onChange={(e) => setMssql({ ...mssql, username: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                            placeholder="edge_reader"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.password")}</div>
                        <input
                            type="password"
                            value={String(mssql.password || "")}
                            onChange={(e) => setMssql({ ...mssql, password: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                            placeholder={t("connections.mssql.passwordPlaceholder")}
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.database")}</div>
                        <input
                            value={mssql.database}
                            onChange={(e) => setMssql({ ...mssql, database: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.table")}</div>
                        <input
                            value={mssql.table}
                            onChange={(e) => setMssql({ ...mssql, table: e.target.value })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.pollInterval")}</div>
                        <input
                            type="number"
                            value={mssql.poll_interval_seconds}
                            onChange={(e) => setMssql({ ...mssql, poll_interval_seconds: Number(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.windowMinutes")}</div>
                        <input
                            type="number"
                            value={mssql.window_minutes}
                            onChange={(e) => setMssql({ ...mssql, window_minutes: Number(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>

                    <label className="space-y-2">
                        <div className="text-sm text-slate-300">{t("connections.mssql.maxRows")}</div>
                        <input
                            type="number"
                            value={mssql.max_rows_per_poll}
                            onChange={(e) => setMssql({ ...mssql, max_rows_per_poll: Number(e.target.value) })}
                            className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-slate-200"
                        />
                    </label>
                </div>

                <div className="flex flex-wrap items-center gap-3 mt-6">
                    <button
                        onClick={() => saveMutation.mutate()}
                        disabled={saveMutation.isPending}
                        className="px-4 py-2 bg-emerald-600 hover:bg-emerald-500 disabled:opacity-60 text-white rounded-lg"
                    >
                        {saveMutation.isPending ? t("common.saving") : t("common.save")}
                    </button>
                    <button
                        onClick={() => testMutation.mutate()}
                        disabled={testMutation.isPending}
                        className="px-4 py-2 bg-slate-700 hover:bg-slate-600 disabled:opacity-60 text-slate-200 rounded-lg"
                    >
                        {testMutation.isPending ? t("connections.common.testing") : t("connections.common.test")}
                    </button>
                </div>
            </div>

            {ErrorComponent}
        </div>
    );
}
