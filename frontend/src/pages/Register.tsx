import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import api from "../api";
import { useT } from "../i18n/I18nProvider";

export default function Register() {
    const t = useT();
    const [email, setEmail] = useState("");
    const [fullName, setFullName] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [success, setSuccess] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setSuccess("");
        setIsLoading(true);

        try {
            // New users are created with viewer role by default for safety
            await api.post("/users", {
                email,
                password,
                full_name: fullName || undefined,
                role: "viewer",
            });
            setSuccess(t("auth.accountCreated"));
            setTimeout(() => navigate("/login"), 1200);
        } catch (err: any) {
            const message =
                err.response?.data?.detail ||
                err.message ||
                t("auth.accountCreateFailed");
            setError(message);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-[#010313] via-[#0a0f1e] to-[#010313] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-emerald-400 to-cyan-400 mb-2">
                        {t("app.name")}
                    </h1>
                    <p className="text-slate-400 text-sm">{t("auth.createNewAccount")}</p>
                </div>

                <div className="bg-slate-900/80 backdrop-blur-xl border border-slate-700/50 rounded-2xl p-8 shadow-2xl">
                    <h2 className="text-2xl font-semibold text-slate-100 mb-6 text-center">
                        {t("auth.signUp")}
                    </h2>

                    {error && (
                        <div className="mb-4 p-3 bg-rose-500/20 border border-rose-500/50 rounded-lg text-rose-200 text-sm">
                            {error}
                        </div>
                    )}
                    {success && (
                        <div className="mb-4 p-3 bg-emerald-500/20 border border-emerald-500/50 rounded-lg text-emerald-200 text-sm">
                            {success}
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {t("auth.fullName")}
                            </label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                                placeholder={t("auth.yourName")}
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {t("auth.emailAddress")}
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                                placeholder="you@example.com"
                                required
                                disabled={isLoading}
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-slate-300 mb-2">
                                {t("auth.password")}
                            </label>
                            <input
                                type="password"
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                                className="w-full px-4 py-3 bg-slate-800/50 border border-slate-700/50 rounded-xl text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500/50"
                                placeholder={t("auth.choosePassword")}
                                required
                                minLength={3}
                                disabled={isLoading}
                            />
                        </div>

                        <button
                            type="submit"
                            disabled={isLoading}
                            className="w-full py-3 px-4 bg-gradient-to-r from-emerald-500 to-emerald-400 hover:from-emerald-400 hover:to-emerald-300 text-slate-900 font-semibold rounded-xl shadow-lg shadow-emerald-500/25 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? t("auth.creatingAccount") : t("auth.createAccount")}
                        </button>
                    </form>

                    <p className="mt-6 text-center text-sm text-slate-400">
                        {t("auth.alreadyHaveAccount")}{" "}
                        <Link to="/login" className="text-emerald-400 hover:text-emerald-300 font-medium">
                            {t("auth.signInLink")}
                        </Link>
                    </p>
                </div>
            </div>
        </div>
    );
}


