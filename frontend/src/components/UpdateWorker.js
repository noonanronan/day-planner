import React, { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import DatePicker from "react-datepicker";
import "react-datepicker/dist/react-datepicker.css";
import { getAllWorkers, updateWorker } from "../services/workerService";

const predefinedRoles = ["KITUP", "AATT", "MT", "ICA"];


const predefinedTimes = [
    { label: "8:00 AM - 4:00 PM", start: new Date().setHours(8, 0), end: new Date().setHours(16, 0) },
    { label: "10:00 AM - 7:00 PM", start: new Date().setHours(10, 0), end: new Date().setHours(19, 0) },
];

const UpdateWorker = () => {
    const { id } = useParams();
    const navigate = useNavigate();
    const [name, setName] = useState("");
    const [selectedRoles, setSelectedRoles] = useState([]); // Updated to handle checkboxes
    const [availability, setAvailability] = useState([]); // Updated for date ranges

    useEffect(() => {
        const fetchWorker = async () => {
            try {
                const data = await getAllWorkers();
                const worker = data.workers.find((worker) => worker.id === parseInt(id));
                if (worker) {
                    setName(worker.name);
                    setSelectedRoles(worker.roles); // Set selected roles
                    setAvailability(
                        worker.availability.map((range) => ({
                            start: new Date(range.start), // Convert to Date objects
                            end: new Date(range.end),
                        }))
                    ); // Set availability
                }
            } catch (error) {
                console.error("Error fetching worker:", error);
            }
        };

        fetchWorker();
    }, [id]);

    const handleRoleChange = (role) => {
        setSelectedRoles((prevRoles) =>
            prevRoles.includes(role)
                ? prevRoles.filter((r) => r !== role) // Remove if already selected
                : [...prevRoles, role] // Add if not selected
        );
    };

    const handleAddAvailability = () => {
        setAvailability([...availability, { start: null, end: null }]);
    };

    const handleAddPredefinedTime = (time) => {
        setAvailability([...availability, { start: new Date(time.start), end: new Date(time.end) }]);
    };

    const handleRemoveAvailability = (index) => {
        setAvailability(availability.filter((_, i) => i !== index));
    };

    const handleDateChange = (index, type, date) => {
        if (date instanceof Date && !isNaN(date)) {
            const updatedAvailability = [...availability];
            updatedAvailability[index][type] = date;
            setAvailability(updatedAvailability);
        } else {
            console.error("Invalid date:", date);
        }
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (availability.some(({ start, end }) => !start || !end)) {
            alert("Please fill out all availability fields.");
            return;
        }

        try {
            const updatedWorker = {
                name,
                roles: selectedRoles,
                availability, // Already formatted as an array of date ranges
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
                    <label className="form-label">Roles</label>
                    <div>
                        {predefinedRoles.map((role) => (
                            <div className="form-check" key={role}>
                                <input
                                    className="form-check-input"
                                    type="checkbox"
                                    id={role}
                                    checked={selectedRoles.includes(role)}
                                    onChange={() => handleRoleChange(role)}
                                />
                                <label className="form-check-label" htmlFor={role}>
                                    {role}
                                </label>
                            </div>
                        ))}
                    </div>
                </div>
                <div className="mb-3">
                    <label className="form-label">Availability</label>
                    <div className="mb-2">
                        {predefinedTimes.map((time, index) => (
                            <button
                                key={index}
                                type="button"
                                className="btn btn-outline-primary btn-sm me-2"
                                onClick={() => handleAddPredefinedTime(time)}
                            >
                                {time.label}
                            </button>
                        ))}
                    </div>
                    {availability.map((range, index) => (
                        <div key={index} className="d-flex align-items-center mb-2">
                            <DatePicker
                                selected={range.start}
                                onChange={(date) => handleDateChange(index, "start", date)}
                                selectsStart
                                startDate={range.start}
                                endDate={range.end}
                                showTimeSelect
                                timeFormat="HH:mm"
                                timeIntervals={30}
                                timeCaption="Time"
                                dateFormat="Pp"
                                placeholderText="Start Time"
                                className="form-control me-2"
                            />
                            <DatePicker
                                selected={range.end}
                                onChange={(date) => handleDateChange(index, "end", date)}
                                selectsEnd
                                startDate={range.start}
                                endDate={range.end}
                                showTimeSelect
                                timeFormat="HH:mm"
                                timeIntervals={30}
                                timeCaption="Time"
                                dateFormat="Pp"
                                placeholderText="End Time"
                                className="form-control me-2"
                            />
                            <button
                                type="button"
                                className="btn btn-danger btn-sm"
                                onClick={() => handleRemoveAvailability(index)}
                            >
                                Remove
                            </button>
                        </div>
                    ))}
                    <button type="button" className="btn btn-secondary btn-sm" onClick={handleAddAvailability}>
                        Add Custom Time
                    </button>
                </div>
                <button type="submit" className="btn btn-primary">Update</button>
            </form>
        </div>
    );
};

export default UpdateWorker;
