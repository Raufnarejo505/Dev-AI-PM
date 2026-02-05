import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../contexts/AuthContext";
import { useT } from "../i18n/I18nProvider";

export default function Login() {
    const t = useT();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [emailError, setEmailError] = useState("");
    const [passwordError, setPasswordError] = useState("");
    const { login } = useAuth();
    const navigate = useNavigate();

    // Email validation
    const validateEmail = (email: string): boolean => {
        const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
        return emailRegex.test(email);
    };

    // Password validation
    const validatePassword = (password: string): boolean => {
        return password.length >= 3; // Minimum 3 characters
    };

    const handleEmailChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setEmail(value);
        if (value && !validateEmail(value)) {
            setEmailError(t("auth.emailInvalid"));
        } else {
            setEmailError("");
        }
    };

    const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const value = e.target.value;
        setPassword(value);
        if (value && !validatePassword(value)) {
            setPasswordError(t("auth.passwordMin3"));
        } else {
            setPasswordError("");
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError("");
        setEmailError("");
        setPasswordError("");

        // Validate inputs
        if (!email) {
            setEmailError(t("auth.emailRequired"));
            return;
        }
        if (!validateEmail(email)) {
            setEmailError(t("auth.emailInvalid"));
            return;
        }
        if (!password) {
            setPasswordError(t("auth.passwordRequired"));
            return;
        }
        if (!validatePassword(password)) {
            setPasswordError(t("auth.passwordMin3"));
            return;
        }

        setIsLoading(true);

        try {
            await login(email, password);
            navigate("/");
        } catch (err: any) {
            // Better error handling for network issues
            let errorMessage = t("auth.loginFailed");
            
            if (err.message) {
                if (err.message.includes("timeout") || err.message.includes("Failed to fetch")) {
                    errorMessage = t("auth.backendNotResponding");
                } else if (err.message.includes("401") || err.message.includes("Invalid")) {
                    errorMessage = t("auth.invalidCredentials");
                } else {
                    errorMessage = err.message;
                }
            } else if (err.response?.data?.detail) {
                errorMessage = err.response.data.detail;
            }
            
            setError(errorMessage);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-white via-[#f7f5ff] to-[#efe9ff] flex items-center justify-center p-4">
            <div className="w-full max-w-md">
                {/* Logo/Title Section */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-purple-700 to-purple-500 mb-2">
                        {t("app.name")}
                    </h1>
                    <p className="text-slate-600 text-sm">{t("app.tagline")}</p>
                </div>

                {/* Login Card */}
                <div className="bg-white/90 backdrop-blur-xl border border-slate-200 rounded-2xl p-8 shadow-xl">
                    <h2 className="text-2xl font-semibold text-slate-900 mb-6 text-center">
                        {t("auth.signIn")}
                    </h2>

                    {/* Error Message */}
                    {error && (
                        <div className="mb-4 p-3 bg-rose-500/20 border border-rose-500/50 rounded-lg text-rose-200 text-sm">
                            <div className="flex items-center gap-2">
                                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                                </svg>
                                <span>{error}</span>
                            </div>
                        </div>
                    )}

                    <form onSubmit={handleSubmit} className="space-y-5">
                        {/* Email Field */}
                        <div>
                            <label htmlFor="email" className="block text-sm font-medium text-slate-700 mb-2">
                                {t("auth.emailAddress")}
                            </label>
                            <input
                                id="email"
                                type="email"
                                value={email}
                                onChange={handleEmailChange}
                                onBlur={() => {
                                    if (email && !validateEmail(email)) {
                                        setEmailError(t("auth.emailInvalid"));
                                    }
                                }}
                                className={`w-full px-4 py-3 bg-white border rounded-xl text-slate-900 placeholder-slate-400 
                                    focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-300
                                    transition-all duration-200
                                    ${emailError ? "border-rose-400 focus:ring-rose-500/20 focus:border-rose-400" : "border-slate-200"}
                                    disabled:opacity-50 disabled:cursor-not-allowed`}
                                placeholder="admin@example.com"
                                required
                                disabled={isLoading}
                                autoComplete="email"
                            />
                            {emailError && (
                                <p className="mt-1 text-xs text-rose-400 flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                    {emailError}
                                </p>
                            )}
                        </div>

                        {/* Password Field */}
                        <div>
                            <label htmlFor="password" className="block text-sm font-medium text-slate-700 mb-2">
                                {t("auth.password")}
                            </label>
                            <input
                                id="password"
                                type="password"
                                value={password}
                                onChange={handlePasswordChange}
                                onBlur={() => {
                                    if (password && !validatePassword(password)) {
                                        setPasswordError(t("auth.passwordMin3"));
                                    }
                                }}
                                className={`w-full px-4 py-3 bg-white border rounded-xl text-slate-900 placeholder-slate-400 
                                    focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-300
                                    transition-all duration-200
                                    ${passwordError ? "border-rose-400 focus:ring-rose-500/20 focus:border-rose-400" : "border-slate-200"}
                                    disabled:opacity-50 disabled:cursor-not-allowed`}
                                placeholder={t("auth.enterPassword")}
                                required
                                disabled={isLoading}
                                autoComplete="current-password"
                            />
                            {passwordError && (
                                <p className="mt-1 text-xs text-rose-400 flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                                        <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                    </svg>
                                    {passwordError}
                                </p>
                            )}
                        </div>

                        {/* Submit Button */}
                        <button
                            type="submit"
                            disabled={isLoading || !!emailError || !!passwordError}
                            className="w-full py-3 px-4 bg-gradient-to-r from-purple-700 to-purple-500 hover:from-purple-600 hover:to-purple-400 
                                text-white font-semibold rounded-xl shadow-lg shadow-purple-500/20
                                transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]
                                disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none
                                flex items-center justify-center gap-2"
                        >
                            {isLoading ? (
                                <>
                                    <svg className="animate-spin h-5 w-5" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                                    </svg>
                                    <span>{t("auth.signingIn")}</span>
                                </>
                            ) : (
                                <span>{t("auth.signIn")}</span>
                            )}
                        </button>
                    </form>

                    {/* Demo Credentials + Sign up link */}
                    <div className="mt-6 pt-6 border-t border-slate-200 space-y-3">
                        <p className="text-xs text-slate-500 text-center">{t("auth.demoCredentials")}</p>
                        <div className="flex flex-col gap-1 text-xs">
                            <div className="flex justify-between items-center p-2 bg-slate-50 rounded border border-slate-200">
                                <span className="text-slate-500">Admin:</span>
                                <span className="text-slate-700 font-mono">admin@example.com / admin123</span>
                            </div>
                            <div className="flex justify-between items-center p-2 bg-slate-50 rounded border border-slate-200">
                                <span className="text-slate-500">Engineer:</span>
                                <span className="text-slate-700 font-mono">engineer@example.com / engineer123</span>
                            </div>
                            <div className="flex justify-between items-center p-2 bg-slate-50 rounded border border-slate-200">
                                <span className="text-slate-500">Viewer:</span>
                                <span className="text-slate-700 font-mono">viewer@example.com / viewer123</span>
                            </div>
                        </div>
                        <p className="text-center text-xs text-slate-500">
                            {t("auth.dontHaveAccount")}{" "}
                            <a href="/register" className="text-purple-700 hover:text-purple-600 font-medium">
                                {t("auth.signUpLink")}
                            </a>
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <p className="text-center text-slate-500 text-xs mt-6">
                    © 2025 {t("app.name")}
                </p>
            </div>
        </div>
    );
}
