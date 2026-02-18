import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

export const sendMessage = async (message, conversationId) => {
    const response = await axios.post(`${API_URL}/chat`, {
        message,
        conversation_id: conversationId,
    });
    return response.data;
};

export const getConversations = async () => {
    const response = await axios.get(`${API_URL}/conversations`);
    return response.data;
};

export const getConversation = async (id) => {
    const response = await axios.get(`${API_URL}/conversations/${id}`);
    return response.data;
};

export const deleteConversation = async (id) => {
    const response = await axios.delete(`${API_URL}/conversations/${id}`);
    return response.data;
};
