import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { BrowserRouter } from "react-router-dom";
import Login from "../pages/Login";
import { AuthProvider } from "../contexts/AuthContext";
import api from "../api";

// Mock API
vi.mock("../api");
const mockedApi = api as any;

describe("Login", () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it("renders login form", () => {
        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
        expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
        expect(screen.getByRole("button", { name: /sign in/i })).toBeInTheDocument();
    });

    it("shows error on invalid credentials", async () => {
        mockedApi.post.mockRejectedValueOnce({
            response: { data: { detail: "Invalid credentials" } },
        });

        render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        const emailInput = screen.getByLabelText(/email/i);
        const passwordInput = screen.getByLabelText(/password/i);
        const submitButton = screen.getByRole("button", { name: /sign in/i });

        fireEvent.change(emailInput, { target: { value: "test@example.com" } });
        fireEvent.change(passwordInput, { target: { value: "wrongpassword" } });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
        });
    });

    it("successfully logs in with valid credentials", async () => {
        mockedApi.post.mockResolvedValueOnce({
            data: {
                access_token: "test-token",
                refresh_token: "test-refresh",
            },
        });

        const { container } = render(
            <BrowserRouter>
                <AuthProvider>
                    <Login />
                </AuthProvider>
            </BrowserRouter>
        );

        const emailInput = screen.getByLabelText(/email/i);
        const passwordInput = screen.getByLabelText(/password/i);
        const submitButton = screen.getByRole("button", { name: /sign in/i });

        fireEvent.change(emailInput, { target: { value: "admin@example.com" } });
        fireEvent.change(passwordInput, { target: { value: "admin123" } });
        fireEvent.click(submitButton);

        await waitFor(() => {
            expect(mockedApi.post).toHaveBeenCalledWith(
                "/users/login",
                expect.any(FormData),
                expect.any(Object)
            );
        });
    });
});

