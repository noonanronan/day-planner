import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createWorker } from "../services/workerService";

const isValidJSON = (input) => {
    try {
        JSON.parse(input);
        return true;
    } catch (error) {
        return false;
    }
};

const CreateWorker = () => {
    const [name, setName] = useState("");
    const [roles, setRoles] = useState("");
    const [availability, setAvailability] = useState("");
    const [isAvailabilityValid, setIsAvailabilityValid] = useState(true); // Track JSON validity
    const navigate = useNavigate();

    const handleAvailabilityChange = (e) => {
        const input = e.target.value;
        setAvailability(input);
        setIsAvailabilityValid(isValidJSON(input));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!isValidJSON(availability)) {
            alert("Invalid JSON format for availability");
            return;
        }

        try {
            const workerData = {
                name,
                roles: roles.split(",").map((role) => role.trim()),
                availability: JSON.parse(availability),
            };
            await createWorker(workerData);
            navigate("/");
        } catch (error) {
            console.error("Error creating worker:", error);
            alert("Failed to create worker. Please check your input format.");
        }
    };

    return (
        <div className="container mt-4">
            <h1 className="text-center mb-4">Create Worker</h1>
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
                        className={`form-control ${isAvailabilityValid ? "" : "is-invalid"}`}
                        rows="5"
                        value={availability}
                        onChange={handleAvailabilityChange}
                        required
                    />
                    {!isAvailabilityValid && (
                        <div className="invalid-feedback">
                            Please enter a valid JSON format.
                        </div>
                    )}
                </div>
                <button type="submit" className="btn btn-success">Create</button>
            </form>
        </div>
    );
};

export default CreateWorker;
