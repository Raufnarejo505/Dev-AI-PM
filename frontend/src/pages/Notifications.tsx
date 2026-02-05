import React, { useState, useEffect } from "react";
import { useMutation } from "@tanstack/react-query";
import api from "../api";
import { useErrorToast } from "../components/ErrorToast";
import { useSSE } from "../hooks/useSSE";
// Using standard HTML elements instead of UI components

export default function NotificationsPage() {
    const { showError, ErrorComponent } = useErrorToast();
    const [testEmail, setTestEmail] = useState<string>("");
    const [notifications, setNotifications] = useState<any[]>([]);
    
    // Subscribe to real-time events via SSE
    useSSE("/ws/events/stream", (message) => {
        console.log("Notification event:", message.type, message.data);
        
        // Add notification to list
        setNotifications((prev) => {
            const newNotification = {
                id: Date.now(),
                type: message.type,
                data: message.data,
                timestamp: new Date(),
            };
            return [newNotification, ...prev].slice(0, 50); // Keep last 50
        });
        
        // Show toast for important events
        if (message.type === "alarm.created" || message.type === "prediction.created") {
            const severity = message.data?.severity || message.data?.status || "info";
            showError(`${message.type}: ${message.data?.message || JSON.stringify(message.data)}`);
        }
    });

    const testEmailMutation = useMutation({
        mutationFn: async (email?: string) => {
            const payload = email ? { to: email } : null;
            const { data } = await api.post("/notifications/test-email", payload);
            return data;
        },
        onSuccess: (data) => {
            if (data.ok) {
                showError("Test email sent successfully!");
            } else {
                showError(`Failed to send test email: ${data.error || "Unknown error"}`);
            }
        },
        onError: (error: any) => {
            showError(`Failed to send test email: ${error.response?.data?.error || error.message || "Unknown error"}`);
        },
    });

    const testWebhookMutation = useMutation({
        mutationFn: async (url: string) => {
            const { data } = await api.post("/notifications/test-webhook", {
                url,
                event_type: "test.event",
            });
            return data;
        },
        onSuccess: (data) => {
            if (data.ok) {
                showError("Test webhook triggered successfully!");
            } else {
                showError(`Failed to trigger webhook: ${data.error || "Unknown error"}`);
            }
        },
        onError: (error: any) => {
            showError(`Failed to trigger webhook: ${error.response?.data?.error || error.message || "Unknown error"}`);
        },
    });

    const handleTestEmail = () => {
        testEmailMutation.mutate(testEmail || undefined);
    };

    const handleTestWebhook = (url: string) => {
        if (!url) {
            showError("Please enter a webhook URL");
            return;
        }
        testWebhookMutation.mutate(url);
    };

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-3xl font-bold text-slate-900">Notifications</h1>
                <p className="text-slate-600 mt-1">Test and manage email notifications and webhooks</p>
            </div>

            {/* Email Notifications */}
            <div className="bg-white/90 border border-slate-200 rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Email Notifications</h2>
                <p className="text-slate-600 text-sm mb-4">
                    Test email notifications. Emails are automatically sent for:
                </p>
                <ul className="text-slate-700 text-sm mb-4 space-y-1 list-disc list-inside">
                    <li>User registration (welcome email)</li>
                    <li>Critical/Warning AI predictions</li>
                    <li>Alarm triggers</li>
                </ul>
                <div className="space-y-4">
                    <div>
                        <label htmlFor="test-email" className="block text-sm text-slate-700 mb-2">Test Email Address (optional)</label>
                        <input
                            id="test-email"
                            type="email"
                            placeholder="tanirajsingh574@gmail.com"
                            value={testEmail}
                            onChange={(e) => setTestEmail(e.target.value)}
                            className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 mt-2 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-300"
                        />
                        <p className="text-xs text-slate-500 mt-1">
                            Leave empty to send to default notification email
                        </p>
                    </div>
                    <button
                        onClick={handleTestEmail}
                        disabled={testEmailMutation.isPending}
                        className="px-6 py-3 bg-purple-700 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                        {testEmailMutation.isPending ? "Sending..." : "Send Test Email"}
                    </button>
                </div>
            </div>

            {/* Webhook Notifications */}
            <div className="bg-white/90 border border-slate-200 rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Webhook Notifications</h2>
                <p className="text-slate-600 text-sm mb-4">
                    Test webhook endpoints. Webhooks are triggered for:
                </p>
                <ul className="text-slate-700 text-sm mb-4 space-y-1 list-disc list-inside">
                    <li>Alarm events (critical/warning)</li>
                    <li>Prediction events (anomalies detected)</li>
                    <li>Machine status changes</li>
                </ul>
                <div className="space-y-4">
                    <div>
                        <label htmlFor="test-webhook-url" className="block text-sm text-slate-700 mb-2">Webhook URL</label>
                        <input
                            id="test-webhook-url"
                            type="url"
                            placeholder="https://your-webhook-endpoint.com/webhook"
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    handleTestWebhook(e.currentTarget.value);
                                }
                            }}
                            className="w-full px-4 py-2 bg-white border border-slate-200 rounded-lg text-slate-900 mt-2 focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-300"
                        />
                    </div>
                    <button
                        onClick={(e) => {
                            const input = document.getElementById("test-webhook-url") as HTMLInputElement;
                            handleTestWebhook(input?.value || "");
                        }}
                        disabled={testWebhookMutation.isPending}
                        className="px-6 py-3 bg-purple-700 hover:bg-purple-600 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                    >
                        {testWebhookMutation.isPending ? "Testing..." : "Test Webhook"}
                    </button>
                </div>
            </div>

            {/* Real-time Notifications Feed */}
            <div className="bg-white/90 border border-slate-200 rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">Real-time Notifications Feed</h2>
                <div className="space-y-2 max-h-96 overflow-y-auto">
                    {notifications.length === 0 ? (
                        <p className="text-slate-600 text-sm">No notifications yet. Events will appear here in real-time.</p>
                    ) : (
                        notifications.map((notif) => (
                            <div
                                key={notif.id}
                                className="bg-slate-50 p-3 rounded-lg border border-slate-200"
                            >
                                <div className="flex items-start justify-between">
                                    <div className="flex-1">
                                        <div className="text-sm font-medium text-slate-900">
                                            {notif.type}
                                        </div>
                                        <div className="text-xs text-slate-500 mt-1">
                                            {notif.timestamp.toLocaleTimeString()}
                                        </div>
                                        <pre className="text-xs text-slate-700 mt-2 bg-white p-2 rounded overflow-x-auto border border-slate-200">
                                            {JSON.stringify(notif.data, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            </div>
                        ))
                    )}
                </div>
            </div>

            {/* API Endpoints Info */}
            <div className="bg-white/90 border border-slate-200 rounded-2xl p-6 shadow-sm">
                <h2 className="text-lg font-semibold text-slate-900 mb-4">API Endpoints</h2>
                <div className="space-y-3 text-sm">
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <code className="text-purple-700">POST /notifications/test-email</code>
                        <p className="text-slate-600 mt-1">Send a test email notification</p>
                        <pre className="text-xs text-slate-600 mt-2 bg-white p-2 rounded border border-slate-200">
{`Body (optional):
{
  "to": "email@example.com"
}`}
                        </pre>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <code className="text-purple-700">POST /notifications/test-webhook</code>
                        <p className="text-slate-600 mt-1">Test a webhook endpoint</p>
                        <pre className="text-xs text-slate-600 mt-2 bg-white p-2 rounded border border-slate-200">
{`Body:
{
  "url": "https://your-webhook.com",
  "event_type": "test.event"
}`}
                        </pre>
                    </div>
                    <div className="bg-slate-50 p-3 rounded-lg border border-slate-200">
                        <p className="text-slate-600">
                            Full API documentation available at:{" "}
                            <a
                                href="http://localhost:8000/docs"
                                target="_blank"
                                rel="noopener noreferrer"
                                className="text-purple-700 hover:underline"
                            >
                                http://localhost:8000/docs
                            </a>
                        </p>
                    </div>
                </div>
            </div>

            {ErrorComponent}
        </div>
    );
}

