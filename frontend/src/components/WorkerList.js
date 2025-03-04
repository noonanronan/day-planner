import React, { useEffect, useState } from "react";
import { getAllWorkers, deleteWorker } from "../services/workerService";
import { useNavigate } from "react-router-dom";
import { format, isWithinInterval, parseISO, isValid, compareAsc } from "date-fns";
import axios from "axios";

const WorkerList = () => {
    const [workers, setWorkers] = useState([]);
    const [templates, setTemplates] = useState([]); // List of uploaded templates
    const [searchQuery, setSearchQuery] = useState(""); // State for search input
    const [selectedTemplate, setSelectedTemplate] = useState(""); // Selected template for schedule generation
    const [fileFormat, setFileFormat] = useState("xlsx");
    const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd")); // Default to today
    const [file, setFile] = useState(null); // For uploading new templates
    const [error, setError] = useState(null); // Error handling for uploads
    const navigate = useNavigate();

    useEffect(() => {
        // Fetch all workers
        const fetchWorkers = async () => {
            try {
                const data = await getAllWorkers();
                setWorkers(data.workers);
            } catch (error) {
                console.error("Error fetching workers:", error);
            }
        };
    
        // Fetch available templates
        const fetchTemplates = async () => {
            try {
                const response = await axios.get("http://127.0.0.1:5001/list-templates"); // Correct endpoint
                console.log("Templates fetched:", response.data.templates); // Debug log
                setTemplates(response.data.templates);
            } catch (error) {
                console.error("Error fetching templates:", error);
            }
        };
    
        fetchWorkers();
        fetchTemplates();
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
        console.log("Selected Date Before Sending:", selectedDate);

        if (!selectedTemplate) {
            alert("Please select a template to generate the schedule.");
            return;
        }
    
        try {
            const response = await axios.post(
                "http://127.0.0.1:5001/generate-schedule",
                { template: selectedTemplate, date: selectedDate }, // Sending date
                {
                    params: { format: fileFormat },
                    responseType: "blob",
                }
            );
    
            const extension = fileFormat === "ods" ? "ods" : "xlsx";
            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", `day_schedule.${extension}`);
            document.body.appendChild(link);
            link.click();
        } catch (error) {
            console.error("Error downloading schedule:", error);
            alert("Failed to download schedule. Please try again.");
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
            setError(null);
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
            alert("File uploaded successfully!");
            setTemplates((prevTemplates) => [...prevTemplates, response.data.filename]); // Add new template to list
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
        const now = new Date();
        const today = new Date(); // Current date
        const todayStart = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 0, 0, 0); // 00:00:00
        const todayEnd = new Date(today.getFullYear(), today.getMonth(), today.getDate(), 23, 59, 59); // 23:59:59
    
        return availability.some((range) => {
            const start = parseISO(range.start);
            const end = parseISO(range.end);
    
            return (
                isValid(start) &&
                isValid(end) &&
                start <= todayEnd && end >= todayStart // Ensure it's within today's range
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

            {/* Upload Template Section */}
            <div className="mb-4">
                <h4>Upload Template</h4>
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

            {/* Select Date */}
            <div className="mb-4">
                <label className="form-label">Select Date:</label>
                <input
                    type="date"
                    className="form-control"
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                />
            </div>

            {/* Select Template and Generate Schedule Section */}
            <div className="mb-4">
                <label htmlFor="templateSelect" className="form-label">
                    Select Template:
                </label>
                <select
                    id="templateSelect"
                    className="form-select"
                    value={selectedTemplate}
                    onChange={(e) => setSelectedTemplate(e.target.value)}
                >
                    <option value="">-- Select a Template --</option>
                    {templates.map((template, index) => (
                        <option key={index} value={template}>
                            {template}
                        </option>
                    ))}
                </select>

                <label htmlFor="fileFormat" className="form-label mt-3">
                    Choose File Format:
                </label>
                <select
                    id="fileFormat"
                    className="form-select"
                    value={fileFormat}
                    onChange={(e) => setFileFormat(e.target.value)}
                >
                    <option value="xlsx">Excel (.xlsx)</option>
                    <option value="ods">OpenDocument (.ods)</option>
                </select>

                <button
                    className="btn btn-primary mt-3"
                    onClick={handleDownloadSchedule}
                >
                    Generate Schedule
                </button>
            </div>

            {/* Search Bar */}
            <div className="mb-4">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Search workers..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

            {/* Worker List */}
            <div className="row g-2 mt-4">
                {sortedWorkers
                    .filter(worker => worker.name.toLowerCase().includes(searchQuery.toLowerCase())) // Filter by name
                    .map((worker) => {
                        const nextAvailability = getNextAvailability(worker.availability);
                        const isInToday = isWorkerAvailableToday(worker.availability);

                        return (
                            <div
                                className={`col-12 col-sm-6 col-md-4 col-lg-3 ${isInToday ? "border border-success" : ""}`}
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
