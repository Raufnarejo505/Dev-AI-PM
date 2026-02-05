import api from "./index";
import { RoleCreate, RoleUpdate, RoleRead } from "../types/api";

export const rolesApi = {
    // List roles
    list: async (): Promise<RoleRead[]> => {
        const { data } = await api.get("/roles");
        return data;
    },

    // Get single role
    get: async (roleId: string): Promise<RoleRead> => {
        const { data } = await api.get(`/roles/${roleId}`);
        return data;
    },

    // Create role
    create: async (payload: RoleCreate): Promise<RoleRead> => {
        const { data } = await api.post("/roles", payload);
        return data;
    },

    // Update role
    update: async (roleId: string, payload: RoleUpdate): Promise<RoleRead> => {
        const { data } = await api.patch(`/roles/${roleId}`, payload);
        return data;
    },

    // Delete role
    delete: async (roleId: string): Promise<void> => {
        await api.delete(`/roles/${roleId}`);
    },

    // Update permissions
    updatePermissions: async (roleId: string, permissions: string[]): Promise<RoleRead> => {
        const { data } = await api.patch(`/roles/${roleId}/permissions`, { permissions });
        return data;
    },
};

