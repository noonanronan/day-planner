import axios from "axios";

const API_URL = "http://127.0.0.1:5001"; // Flask backend URL

// Axios instance for reusable configurations
const axiosInstance = axios.create({
    baseURL: API_URL,
    headers: {
        "Content-Type": "application/json", // Default header
    },
});

// Fetch all workers
export const getAllWorkers = async () => {
    try {
        const response = await axiosInstance.get("/workers");
        return response.data;
    } catch (error) {
        console.error("Error fetching workers:", error.response?.data || error.message);
        throw error.response?.data || error.message; // Propagate error for handling
    }
};

// Create a new worker
export const createWorker = async (workerData) => {
    try {
        const response = await axiosInstance.post("/workers", workerData);
        return response.data;
    } catch (error) {
        console.error("Error creating worker:", error.response?.data || error.message);
        throw error.response?.data || error.message; 
    }
};


// Update a worker by ID
export const updateWorker = async (id, workerData) => {
    try {
        const response = await axiosInstance.put(`/workers/${id}`, workerData);
        return response.data;
    } catch (error) {
        console.error("Error updating worker:", error.response?.data || error.message);
        throw error.response?.data || error.message; 
    }
};

// Delete a worker by ID
export const deleteWorker = async (id) => {
    try {
        const response = await axiosInstance.delete(`/workers/${id}`);
        return response.data;
    } catch (error) {
        console.error("Error deleting worker:", error.response?.data || error.message);
        throw error.response?.data || error.message; 
    }
};

// General API request 
export const apiRequest = async (method, endpoint, data = null) => {
    try {
        const response = await axiosInstance({
            method,
            url: endpoint,
            data,
        });
        return response.data;
    } catch (error) {
        console.error(`Error with ${method.toUpperCase()} request to ${endpoint}:`, error.response?.data || error.message);
        throw error.response?.data || error.message; 
    }
};
