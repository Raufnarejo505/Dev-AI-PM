import React from "react";
import ReactDOM from "react-dom/client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import App from "./App";
import "./styles.css";
import { useBackendStore } from "./store/backendStore";
import { I18nProvider } from "./i18n/I18nProvider";
import { getInitialLanguage, tRaw } from "./i18n";

// Create QueryClient at the TOP LEVEL - before any components
const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            retry: 1,
            refetchOnWindowFocus: false,
            staleTime: 5000,
        },
    },
});

// Error boundary for better error handling
class ErrorBoundary extends React.Component<
  { children: React.ReactNode },
  { hasError: boolean; error: Error | null }
> {
  constructor(props: { children: React.ReactNode }) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error("React Error Boundary caught:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      const lang = getInitialLanguage();
      return (
        <div style={{ 
          padding: "40px", 
          background: "#010313", 
          color: "white", 
          minHeight: "100vh",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center"
        }}>
          <h1 style={{ color: "#ef4444", marginBottom: "20px" }}>{tRaw(lang, "errors.appErrorTitle")}</h1>
          <p style={{ marginBottom: "10px" }}>{tRaw(lang, "errors.appErrorMessage")}</p>
          {this.state.error && (
            <details style={{ marginTop: "20px", maxWidth: "600px" }}>
              <summary style={{ cursor: "pointer", color: "#94a3b8" }}>{tRaw(lang, "errors.errorDetails")}</summary>
              <pre style={{ 
                background: "#1e293b", 
                padding: "15px", 
                borderRadius: "8px",
                overflow: "auto",
                marginTop: "10px",
                fontSize: "12px"
              }}>
                {this.state.error.toString()}
                {this.state.error.stack && (
                  <>
                    {"\n\n"}
                    {this.state.error.stack}
                  </>
                )}
              </pre>
            </details>
          )}
          <button
            onClick={() => window.location.reload()}
            style={{
              marginTop: "20px",
              padding: "10px 20px",
              background: "#10b981",
              color: "white",
              border: "none",
              borderRadius: "8px",
              cursor: "pointer",
              fontSize: "16px"
            }}
          >
            {tRaw(lang, "errors.refreshPage")}
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

const rootElement = document.getElementById("root");
if (!rootElement) {
  const lang = getInitialLanguage();
  throw new Error(tRaw(lang, "errors.rootNotFound"));
}

// Start backend health checker
useBackendStore.getState().startHealthCheck();

// QueryClientProvider MUST be at the root level
ReactDOM.createRoot(rootElement).render(
  <QueryClientProvider client={queryClient}>
    <I18nProvider>
      <ErrorBoundary>
        <App />
      </ErrorBoundary>
    </I18nProvider>
  </QueryClientProvider>
);

