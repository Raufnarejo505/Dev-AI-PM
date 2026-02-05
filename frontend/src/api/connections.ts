import api from "./index";

export interface EdgePCConfig {
    host: string;
    port: number;
    username: string;
}

export interface MSSQLConfig {
    enabled: boolean;
    host: string;
    port: number;
    username: string;
    password?: string | null;
    database: string;
    table: string;
    poll_interval_seconds: number;
    window_minutes: number;
    max_rows_per_poll: number;
}

export interface ConnectionsRead {
    edge_pc?: EdgePCConfig | null;
    mssql: MSSQLConfig;
}

export interface ConnectionsUpdate {
    edge_pc?: EdgePCConfig | null;
    mssql?: Partial<MSSQLConfig> | null;
}

export interface MSSQLTestResponse {
    ok: boolean;
    message: string;
}

export const connectionsApi = {
    get: async (): Promise<ConnectionsRead> => {
        const { data } = await api.get("/connections");
        return data;
    },

    update: async (payload: ConnectionsUpdate): Promise<ConnectionsRead> => {
        const { data } = await api.put("/connections", payload);
        return data;
    },

    testMssql: async (payload?: { config?: MSSQLConfig }): Promise<MSSQLTestResponse> => {
        const { data } = await api.post("/connections/test/mssql", payload || {});
        return data;
    },
};
