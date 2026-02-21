import axios from 'axios';

const API_URL = 'http://localhost:8000/api';

// Create an Axios instance
const api = axios.create({
    baseURL: API_URL,
});

// Add a request interceptor to attach the JWT token
api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('token');
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

export const login = async (email, password) => {
    const formData = new URLSearchParams();
    formData.append('username', email); // OAuth2 expects 'username'
    formData.append('password', password);
    const response = await api.post('/auth/login', formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
};

export const signup = async (email, password) => {
    const response = await api.post('/auth/signup', { email, password });
    return response.data;
};

export const getUser = async () => {
    const response = await api.get('/auth/me');
    return response.data;
};

export const sendMessage = async (message, conversationId, file = null) => {
    const formData = new FormData();
    formData.append('message', message);
    if (conversationId) {
        formData.append('conversation_id', conversationId);
    }
    if (file) {
        formData.append('file', file);
    }
    const response = await api.post(`/chat`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
        timeout: 120000, // 2 minute timeout for PDF processing
    });
    return response.data;
};

export const getConversations = async () => {
    const response = await api.get(`/conversations`);
    return response.data;
};

export const getConversation = async (id) => {
    const response = await api.get(`/conversations/${id}`);
    return response.data;
};

export const deleteConversation = async (id) => {
    const response = await api.delete(`/conversations/${id}`);
    return response.data;
};

export const logout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
};
