import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { getAllWorkers, updateWorker } from "../services/workerService";

const isValidJSON = (input) => {
    try {
        JSON.parse(input);
        return true;
    } catch (error) {
        return false;
    }
};

const UpdateWorker = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [roles, setRoles] = useState("");
    const [availability, setAvailability] = useState("");

    useEffect(() => {
        const fetchWorker = async () => {
            try {
                const data = await getAllWorkers();
                const worker = data.workers.find((worker) => worker.id === parseInt(id));
                if (worker) {
                    setName(worker.name);
                    setRoles(worker.roles.join(", "));
                    setAvailability(JSON.stringify(worker.availability, null, 2));
                }
            } catch (error) {
                console.error("Error fetching worker:", error);
            }
        };

        fetchWorker();
    }, [id]);

    const handleSubmit = async (e) => {
        e.preventDefault();

        // Validate JSON format for availability
        if (!isValidJSON(availability)) {
            alert("Invalid JSON format for availability");
            return;
        }

        try {
            const updatedWorker = {
                name,
                roles: roles.split(",").map(role => role.trim()),
                availability: JSON.parse(availability),
            };
            await updateWorker(id, updatedWorker);
            navigate("/");
        } catch (error) {
            console.error("Error updating worker:", error);
            alert("Failed to update worker. Please check your input format.");
        }
    };

    return (
        <div className="container mt-4">
            <h1 className="text-center mb-4">Update Worker</h1>
            <form onSubmit={handleSubmit}>
                <div className="mb-3">
                    <label className="form-label">Name</label>
                    <input
                        type="text"
                        className="form-control"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label className="form-label">Roles (comma-separated)</label>
                    <input
                        type="text"
                        className="form-control"
                        value={roles}
                        onChange={(e) => setRoles(e.target.value)}
                        required
                    />
                </div>
                <div className="mb-3">
                    <label className="form-label">Availability (JSON format)</label>
                    <textarea
                        className="form-control"
                        rows="5"
                        value={availability}
                        onChange={(e) => setAvailability(e.target.value)}
                        required
                    />
                </div>
                <button type="submit" className="btn btn-primary">Update</button>
            </form>
        </div>
    );
};

export default UpdateWorker;
