import axios from "axios";

const API_URL = "http://127.0.0.1:5001"; // Flask backend URL

export const getAllWorkers = async () => {
    try {
        const response = await axios.get(`${API_URL}/workers`);
        return response.data;
    } catch (error) {
        console.error("Error fetching workers:", error);
        throw error;
    }
};

export const createWorker = async (workerData) => {
    try {
        const response = await axios.post(`${API_URL}/workers`, workerData);
        return response.data;
    } catch (error) {
        console.error("Error creating worker:", error);
        throw error;
    }
};

export const updateWorker = async (id, workerData) => {
    try {
        const response = await axios.put(`${API_URL}/workers/${id}`, workerData);
        return response.data;
    } catch (error) {
        console.error("Error updating worker:", error);
        throw error;
    }
};

export const deleteWorker = async (id) => {
    try {
        const response = await axios.delete(`${API_URL}/workers/${id}`);
        return response.data;
    } catch (error) {
        console.error("Error deleting worker:", error);
        throw error;
    }
};
