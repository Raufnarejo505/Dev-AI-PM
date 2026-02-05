import React, { useState, useEffect } from "react";

interface ErrorToastProps {
    message: string;
    onDismiss: () => void;
}

export function ErrorToast({ message, onDismiss }: ErrorToastProps) {
    useEffect(() => {
        const timer = setTimeout(() => {
            onDismiss();
        }, 5000);
        return () => clearTimeout(timer);
    }, [onDismiss]);

    return (
        <div className="fixed bottom-4 right-4 bg-rose-500/90 border border-rose-400/40 rounded-lg px-4 py-3 shadow-lg backdrop-blur z-50 flex items-center gap-3 min-w-[300px]">
            <span className="text-rose-100 text-sm flex-1">{message}</span>
            <button
                onClick={onDismiss}
                className="text-rose-200 hover:text-white transition"
                aria-label="Dismiss"
            >
                ✕
            </button>
        </div>
    );
}

export function useErrorToast() {
    const [error, setError] = useState<string | null>(null);

    const showError = (message: string) => {
        setError(message);
    };

    const ErrorComponent = error ? (
        <ErrorToast message={error} onDismiss={() => setError(null)} />
    ) : null;

    return { showError, ErrorComponent };
}

