import api from "./index";
import { TicketCreate, TicketUpdate, TicketRead, CommentCreate, CommentRead } from "../types/api";

export const ticketsApi = {
    // List tickets
    list: async (): Promise<TicketRead[]> => {
        const { data } = await api.get("/tickets");
        return data;
    },

    // Get single ticket
    get: async (ticketId: string): Promise<TicketRead> => {
        const { data } = await api.get(`/tickets/${ticketId}`);
        return data;
    },

    // Create ticket
    create: async (payload: TicketCreate): Promise<TicketRead> => {
        const { data } = await api.post("/tickets", payload);
        return data;
    },

    // Update ticket
    update: async (ticketId: string, payload: TicketUpdate): Promise<TicketRead> => {
        const { data } = await api.patch(`/tickets/${ticketId}`, payload);
        return data;
    },

    // Add comment to ticket
    addComment: async (ticketId: string, payload: CommentCreate): Promise<CommentRead> => {
        const { data } = await api.post(`/tickets/${ticketId}/comments`, payload);
        return data;
    },

    // Get ticket comments
    getComments: async (ticketId: string): Promise<CommentRead[]> => {
        const { data } = await api.get(`/tickets/${ticketId}/comments`);
        return data;
    },
};

