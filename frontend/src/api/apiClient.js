// api/apiClient.js
import axios from 'axios';

const apiClient = axios.create({
    baseURL: 'http://localhost:8001', // URL FastAPI-сервера
    headers: {
        'Content-Type': 'application/json',
    },
});

// Интерцептор для добавления JWT-токена
// apiClient.interceptors.request.use(
//     (config) => {
//         const token = localStorage.getItem('token');
//         if (token) {
//             config.headers.Authorization = `Bearer ${token}`;
//         }
//         return config;
//     },
//     (error) => Promise.reject(error)
// );

// // Интерцептор для обработки ошибок
// apiClient.interceptors.response.use(
//     (response) => response,
//     (error) => {
//         const message = error.response?.data?.detail || 'Произошла ошибка при выполнении запроса';
//         return Promise.reject(new Error(message));
//     }
// );

export default apiClient;