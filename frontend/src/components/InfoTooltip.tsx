import React, { useState } from "react";

interface InfoTooltipProps {
    content: string;
    className?: string;
}

export const InfoTooltip: React.FC<InfoTooltipProps> = ({ content, className = "" }) => {
    const [isVisible, setIsVisible] = useState(false);

    return (
        <span className={`relative inline-flex items-center ${className}`}>
            <button
                type="button"
                className="text-slate-400 hover:text-slate-300 transition-colors cursor-help"
                onMouseEnter={() => setIsVisible(true)}
                onMouseLeave={() => setIsVisible(false)}
                onClick={(e) => {
                    e.preventDefault();
                    e.stopPropagation();
                }}
                aria-label="Information"
            >
                <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                    xmlns="http://www.w3.org/2000/svg"
                >
                    <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                </svg>
            </button>
            {isVisible && (
                <div
                    className="absolute z-50 px-3 py-2 text-xs text-slate-100 bg-slate-800 border border-slate-600 rounded-lg shadow-xl whitespace-normal max-w-xs left-1/2 transform -translate-x-1/2 bottom-full mb-2"
                    onMouseEnter={() => setIsVisible(true)}
                    onMouseLeave={() => setIsVisible(false)}
                >
                    {content}
                    <div className="absolute left-1/2 transform -translate-x-1/2 top-full w-0 h-0 border-l-4 border-r-4 border-t-4 border-transparent border-t-slate-800" />
                </div>
            )}
        </span>
    );
};

