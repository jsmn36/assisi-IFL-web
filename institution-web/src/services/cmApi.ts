import axios from 'axios';

// CM admin endpoints live at /cm/admin (not under /api/v1). Strip the
// /api/v1 suffix from VITE_API_URL if present.
const _cmEnv = (import.meta.env.VITE_API_URL ?? '').toString();
const _cmRoot = _cmEnv.replace(/\/?api\/v1\/?$/, '');
const BASE_URL = `${_cmRoot}/cm/admin`;

export interface ChannelMapping {
    mapping_id: string;
    channel: string;
    property_id: string;
    room_type_id: number;
    channel_room_id: string;
}

export interface CreateMappingPayload {
    channel: string;
    property_id: string;
    room_type_id: number;
    channel_room_id: string;
}

export const cmApi = {
    getMappings: async (): Promise<ChannelMapping[]> => {
        const response = await axios.get(`${BASE_URL}/mappings`);
        return response.data;
    },

    createMapping: async (payload: CreateMappingPayload): Promise<{ mapping_id: string }> => {
        const response = await axios.post(`${BASE_URL}/mappings`, payload);
        return response.data;
    },

    deleteMapping: async (mappingId: string): Promise<void> => {
        await axios.delete(`${BASE_URL}/mappings/${mappingId}`);
    }
};
