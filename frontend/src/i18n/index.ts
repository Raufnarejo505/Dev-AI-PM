import { de } from "./de";

export type Language = "de";

type Dict = typeof de;

const dictionaries: Record<Language, Dict> = {
    de,
};

const defaultLanguage: Language = "de";

export function getInitialLanguage(): Language {
    const stored = localStorage.getItem("lang");
    if (stored === "de") return "de";
    return defaultLanguage;
}

export function setStoredLanguage(lang: Language) {
    localStorage.setItem("lang", lang);
}

export function tRaw(lang: Language, key: string): string {
    const dict = dictionaries[lang] || dictionaries[defaultLanguage];
    const parts = key.split(".");
    let cur: any = dict;
    for (const p of parts) {
        cur = cur?.[p];
    }
    if (typeof cur === "string") return cur;
    return key;
}

export { de };
