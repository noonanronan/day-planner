import React, { useEffect, useState } from "react";
import { getAllWorkers, deleteWorker } from "../services/workerService";
import { useNavigate } from "react-router-dom";
import { format, isWithinInterval, parseISO, isValid, compareAsc } from "date-fns";

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
            setWorkers(workers.filter((worker) => worker.id !== id));
        } catch (error) {
            console.error("Error deleting worker:", error);
            alert("Failed to delete worker.");
        }
    };

    const getNextAvailability = (availability) => {
        const now = new Date();
        const nextDates = availability
            .map((range) => {
                const start = parseISO(range.start);
                return isValid(start) && compareAsc(start, now) >= 0 ? start : null;
            })
            .filter((date) => date !== null)
            .sort((a, b) => compareAsc(a, b));

        return nextDates.length > 0 ? nextDates[0] : null;
    };

    const isWorkerAvailableToday = (availability) => {
        const today = new Date();
        return availability.some((range) => {
            const start = parseISO(range.start);
            const end = parseISO(range.end);
            return (
                isValid(start) &&
                isValid(end) &&
                isWithinInterval(today, { start, end })
            );
        });
    };

    // Sort workers: those available today first, followed by others based on next availability
    const sortedWorkers = [...workers].sort((a, b) => {
        const aAvailableToday = isWorkerAvailableToday(a.availability);
        const bAvailableToday = isWorkerAvailableToday(b.availability);

        if (aAvailableToday && !bAvailableToday) return -1;
        if (!aAvailableToday && bAvailableToday) return 1;

        const aNext = getNextAvailability(a.availability);
        const bNext = getNextAvailability(b.availability);

        if (aNext && bNext) return compareAsc(aNext, bNext);
        if (aNext && !bNext) return -1;
        if (!aNext && bNext) return 1;

        return 0;
    });

    return (
        <div className="container mt-4">
            <h1 className="text-center mb-4">Worker List</h1>
            <div className="row g-2">
                {sortedWorkers.map((worker) => {
                    const nextAvailability = getNextAvailability(worker.availability);
                    const isInToday = isWorkerAvailableToday(worker.availability);

                    return (
                        <div
                            className={`col-12 col-sm-6 col-md-4 col-lg-3 ${
                                isInToday ? "border border-success" : ""
                            }`}
                            key={worker.id}
                        >
                            <div className="card h-100 shadow-sm">
                                <div className="card-body p-2">
                                    <h6 className="card-title mb-2">
                                        {worker.name}
                                        {isInToday && (
                                            <span className="badge bg-success ms-2">In Today</span>
                                        )}
                                    </h6>
                                    <p className="card-text mb-2">
                                        <strong>Roles:</strong> {worker.roles.join(", ")}
                                    </p>
                                    <p className="card-text mb-2">
                                        <strong>Next Availability:</strong>{" "}
                                        {isInToday
                                            ? "In Today"
                                            : nextAvailability
                                            ? format(nextAvailability, "MMM dd, yyyy HH:mm")
                                            : "No upcoming availability"}
                                    </p>
                                    <div className="d-flex justify-content-between">
                                        <button
                                            className="btn btn-primary btn-sm"
                                            onClick={() => navigate(`/update-worker/${worker.id}`)}
                                        >
                                            Update
                                        </button>
                                        <button
                                            className="btn btn-danger btn-sm"
                                            onClick={() => handleDelete(worker.id)}
                                        >
                                            Delete
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default WorkerList;
