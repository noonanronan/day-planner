import axios from "axios";

const API_URL = (process.env.REACT_APP_API_URL || "").replace(/\/+$/, "");

// Axios instance for reusable configurations
const axiosInstance = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Fetch all workers
export const getAllWorkers = async () => {
  const { data } = await axiosInstance.get("/workers");
  return data;
};

// Create a new worker
export const createWorker = async (workerData) => {
  const { data } = await axiosInstance.post("/workers", workerData);
  return data;
};


// Update a worker by ID
export const updateWorker = async (id, workerData) => {
  const { data } = await axiosInstance.put(`/workers/${id}`, workerData);
  return data;
};


// Delete a worker by ID
export const deleteWorker = async (id) => {
  const { data } = await axiosInstance.delete(`/workers/${id}`);
  return data;
};


// General API request 
export const apiRequest = async (method, endpoint, data = null) => {
  const url = endpoint.startsWith("/") ? endpoint : `/${endpoint}`;
  const { data: resp } = await axiosInstance({ method, url, data });
  return resp;
};

// Upload a template (multipart)
export const uploadTemplate = async (formData) => {
  const { data } = await axiosInstance.post("/upload-excel", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// Upload worker availability (multipart)
export const uploadAvailability = async (formData) => {
  const { data } = await axiosInstance.post("/upload-worker-availability", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

// Generate schedule (returns a Blob)
export const generateSchedule = async (payload) => {
  const resp = await axiosInstance.post("/generate-schedule", payload, {
    responseType: "blob",
  });
  return resp.data; // Blob
};
