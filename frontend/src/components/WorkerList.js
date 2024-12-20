import React, { useEffect, useState } from "react";
import { getAllWorkers, deleteWorker } from "../services/workerService";
import { useNavigate } from "react-router-dom";

const WorkerList = () => {
    const [workers, setWorkers] = useState([]);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchWorkers = async () => {
            try {
                const data = await getAllWorkers();
                setWorkers(data.workers);
            } catch (error) {
                console.error("Error fetching workers:", error);
            }
        };

        fetchWorkers();
    }, []);

    const handleDelete = async (id) => {
        try {
            await deleteWorker(id);
            setWorkers(workers.filter(worker => worker.id !== id));
        } catch (error) {
            console.error("Error deleting worker:", error);
            alert("Failed to delete worker.");
        }
    };

    return (
        <div className="container mt-4">
            <h1 className="text-center mb-4">Worker List</h1>
            <div className="row">
                {workers.map((worker) => (
                    <div className="col-md-4" key={worker.id}>
                        <div className="card mb-4 shadow-sm">
                            <div className="card-body">
                                <h5 className="card-title">{worker.name}</h5>
                                <p className="card-text">
                                    <strong>Roles:</strong> {worker.roles.join(", ")} <br />
                                    <strong>Availability:</strong> {JSON.stringify(worker.availability)}
                                </p>
                                <button
                                    className="btn btn-primary me-2"
                                    onClick={() => navigate(`/update-worker/${worker.id}`)}
                                >
                                    Update
                                </button>
                                <button
                                    className="btn btn-danger"
                                    onClick={() => handleDelete(worker.id)}
                                >
                                    Delete
                                </button>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};


export default WorkerList;
