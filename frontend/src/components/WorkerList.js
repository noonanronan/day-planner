import React, { useEffect, useState } from "react";
import { getAllWorkers, deleteWorker } from "../services/workerService";
import { useNavigate } from "react-router-dom";
import { format, isWithinInterval, parseISO, isValid, compareAsc } from "date-fns";
import axios from "axios";

const WorkerList = () => {
    const [workers, setWorkers] = useState([]);
    const [file, setFile] = useState(null); // State to manage the file
    const [uploadResponse, setUploadResponse] = useState(null); // To display response from upload
    const [error, setError] = useState(""); // Error state for file upload
    const navigate = useNavigate();
    const [fileFormat, setFileFormat] = useState('xlsx');

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

    const handleDownloadSchedule = async () => {
        try {
            const response = await axios.post(
                `http://127.0.0.1:5001/generate-schedule?format=${fileFormat}`,
                {},
                {
                    responseType: 'blob', // Important for downloading files
                }
            );
    
            const extension = fileFormat === 'ods' ? 'ods' : 'xlsx';
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', `day_schedule.${extension}`);
            document.body.appendChild(link);
            link.click();
        } catch (error) {
            console.error('Error downloading schedule:', error);
            alert('Failed to download schedule. Please try again.');
        }
    };
    
    const handleFileChange = (e) => {
        const selectedFile = e.target.files[0];
        if (
            selectedFile &&
            (selectedFile.type.includes("spreadsheet") ||
                selectedFile.name.endsWith(".xlsx") ||
                selectedFile.name.endsWith(".ods"))
        ) {
            setFile(selectedFile);
            setError("");
        } else {
            setFile(null);
            setError("Please select a valid Excel (.xlsx) or ODS (.ods) file.");
        }
    };

    const handleUpload = async () => {
        if (!file) {
            setError("No file selected. Please select a file to upload.");
            return;
        }

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await axios.post(
                "http://127.0.0.1:5001/upload-excel",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );
            setUploadResponse(response.data.data);
            alert("File uploaded successfully!");
        } catch (error) {
            console.error("Error uploading file:", error);
            setError("Failed to upload the file. Please check the format and try again.");
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

            {/* File format and download schedule */}
            <div className="mb-4">
                <label htmlFor="fileFormat">Choose File Format: </label>
                <select
                    id="fileFormat"
                    value={fileFormat}
                    onChange={(e) => setFileFormat(e.target.value)}
                >
                    <option value="xlsx">Excel (.xlsx)</option>
                    <option value="ods">OpenDocument (.ods)</option>
                </select>
                <button className="btn btn-primary ms-2" onClick={handleDownloadSchedule}>
                    Download Schedule
                </button>
            </div>

            {/* File upload */}
            <div className="mb-4">
                <h4>Upload Excel File</h4>
                <input
                    type="file"
                    className="form-control mb-2"
                    accept=".xlsx,.ods"
                    onChange={handleFileChange}
                />
                <button className="btn btn-primary" onClick={handleUpload}>
                    Upload File
                </button>
                {error && <p className="text-danger mt-2">{error}</p>}
            </div>

            {/* Worker List */}
            <div className="row g-2 mt-4">
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
                                            onClick={() =>
                                                navigate(`/update-worker/${worker.id}`)
                                            }
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