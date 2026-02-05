import React from "react";
import { getInitialLanguage, Language, setStoredLanguage, tRaw } from "./index";

type I18nContextValue = {
    language: Language;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
};

const I18nContext = React.createContext<I18nContextValue | null>(null);

export function I18nProvider({ children }: { children: React.ReactNode }) {
    const [language, setLanguageState] = React.useState<Language>(() => getInitialLanguage());

    const setLanguage = React.useCallback((lang: Language) => {
        setLanguageState(lang);
        setStoredLanguage(lang);
    }, []);

    const t = React.useCallback(
        (key: string) => {
            return tRaw(language, key);
        },
        [language]
    );

    const value = React.useMemo<I18nContextValue>(() => ({ language, setLanguage, t }), [language, setLanguage, t]);

    return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n() {
    const ctx = React.useContext(I18nContext);
    if (!ctx) {
        throw new Error("I18nProvider is missing");
    }
    return ctx;
}

export function useT() {
    return useI18n().t;
}
