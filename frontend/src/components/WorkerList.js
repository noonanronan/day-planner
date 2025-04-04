import React, { useEffect, useState } from "react";
import { getAllWorkers, deleteWorker } from "../services/workerService";
import { useNavigate } from "react-router-dom";
import { format, parseISO, isValid, compareAsc, isWithinInterval } from "date-fns";
import axios from "axios";

const WorkerList = () => {
    const [workers, setWorkers] = useState([]);
    const [templates, setTemplates] = useState([]);
    const [searchQuery, setSearchQuery] = useState("");
    const [selectedTemplate, setSelectedTemplate] = useState("");
    const [selectedDate, setSelectedDate] = useState(format(new Date(), "yyyy-MM-dd"));
    const [file, setFile] = useState(null);
    const [error, setError] = useState(null);
    const [showUploadSection, setShowUploadSection] = useState(false);
    const [morningIcaCount, setMorningIcaCount] = useState(4);
    const [afternoonIcaCount, setAfternoonIcaCount] = useState(4);
    const navigate = useNavigate();

    // const handleLogout = () => {
    //     localStorage.removeItem("isAuthenticated");
    //     navigate("/");
    // };    

    useEffect(() => {
        const fetchWorkers = async () => {
            try {
                const data = await getAllWorkers();
                const now = new Date();
    
                const cleanedWorkers = data.workers.map((worker) => {
                    const filteredAvailability = worker.availability
                        .map(({ start, end }) => ({
                            start,
                            end,
                        }))
                        .filter(({ end }) => new Date(end) >= now);
    
                    return { ...worker, availability: filteredAvailability };
                });
    
                setWorkers(cleanedWorkers);
            } catch (error) {
                console.error("Error fetching workers:", error);
            }
        };
    
        const fetchTemplates = async () => {
            try {
                const response = await axios.get("https://ronannoonan.pythonanywhere.com/list-templates");
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
            setWorkers((prev) => prev.filter((worker) => worker.id !== id));
        } catch (error) {
            alert(error.message); 
        }
    };    
    

    const handleDownloadSchedule = async () => {
        if (!selectedTemplate) {
            alert("Please select a template to generate the schedule.");
            return;
        }

        try {
            const response = await axios.post(
                "https://ronannoonan.pythonanywhere.com/generate-schedule",
                {
                  template: selectedTemplate,
                  date: selectedDate,
                  ica_morning_count: morningIcaCount,
                  ica_afternoon_count: afternoonIcaCount,
                },
                {
                  responseType: "blob",
                }
              );
              
            

            const url = window.URL.createObjectURL(new Blob([response.data]));
            const link = document.createElement("a");
            link.href = url;
            link.setAttribute("download", "day_schedule.xlsx");
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
            (selectedFile.name.endsWith(".xlsx") || selectedFile.name.endsWith(".ods"))
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
                "https://ronannoonan.pythonanywhere.com/upload-excel",
                formData,
                {
                    headers: {
                        "Content-Type": "multipart/form-data",
                    },
                }
            );
            alert("File uploaded successfully!");
            setTemplates((prevTemplates) => [...prevTemplates, response.data.filename]);
        } catch (error) {
            console.error("Error uploading file:", error);
            setError("Failed to upload the file. Please check the format and try again.");
        }
    };

    // // 🔹 Helper: Check if worker is in today
    // const isWorkerAvailableToday = (availability) => {
    //     const today = new Date();
    //     const todayStart = new Date(today.setHours(0, 0, 0, 0));
    //     const todayEnd = new Date(today.setHours(23, 59, 59, 999));
    //     return availability.some((range) => {
    //         const start = parseISO(range.start);
    //         const end = parseISO(range.end);
    //         return isValid(start) && isValid(end) && isWithinInterval(today, { start, end });
    //     });
    // };


    // 🔹 Helper: Get the first future availability date
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


    // 🔹 Helper: Get today's availability range (for showing correct time)
    const getTodayAvailability = (availability) => {
        const today = new Date();
        today.setHours(0, 0, 0, 0); // Ensure we're checking full-day range
        const todayEnd = new Date(today);
        todayEnd.setHours(23, 59, 59, 999);
    
        return availability.find(({ start, end }) => {
            const startTime = parseISO(start);
            const endTime = parseISO(end);
    
            return (
                isValid(startTime) &&
                isValid(endTime) &&
                startTime <= todayEnd &&
                endTime >= today // Ensures the worker is available **within today**
            );
        });
    };
    

    // 🔹 Helper: Check if a worker has future availability
    const hasFutureAvailability = (availability) => {
        const now = new Date();
        return availability.some(({ start }) => {
            const startDate = parseISO(start);
            return isValid(startDate) && compareAsc(startDate, now) > 0;
        });
    };
    
    // 🔹 Helper: Get status (today, future, none)
    const getAvailabilityStatus = (availability) => {
        const todayAvailability = getTodayAvailability(availability);
        if (todayAvailability) return "today";
        if (hasFutureAvailability(availability)) return "future";
        return "none";
    };
    
    


    // 🔹 Sort workers: Today first, then future, then none
    const sortedWorkers = [...workers].sort((a, b) => {
        const aAvailableToday = getTodayAvailability(a.availability);
        const bAvailableToday = getTodayAvailability(b.availability);
    
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
            {/* Page Header */}
            <div className="d-flex justify-content-between align-items-center mb-3">
            
                <h1 className="mb-0">Instructor List</h1>
                <button
                    className="btn btn-outline-secondary btn-sm"
                    onClick={() => setShowUploadSection(!showUploadSection)}
                >
                    {showUploadSection ? "Hide Template Upload" : "Show Template Upload"}
                </button>
            </div>

            {/* Upload Template Section */}
            {showUploadSection && (
                <div className="card p-3 mb-4">
                    <h5 className="mb-3">Upload Template</h5>
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
            )}

            {/* Controls for Date & Template Selection */}
            <div className="card p-3 mb-4">
                <div className="row g-3 align-items-center">
                    <div className="col-md-4">
                        <label className="form-label">Select Date:</label>
                        <input
                            type="date"
                            className="form-control"
                            value={selectedDate}
                            onChange={(e) => setSelectedDate(e.target.value)}
                        />
                    </div>
                    <div className="col-md-6">
                        <label className="form-label">Select Template:</label>
                        <select
                            className="form-select"
                            value={selectedTemplate}
                            onChange={(e) => setSelectedTemplate(e.target.value)}
                        >
                            <option value="">-- Choose Template --</option>
                            {templates.map((template, index) => (
                                <option key={index} value={template}>
                                    {template}
                                </option>
                            ))}
                        </select>
                    </div>
                    <div className="col-md-3">
                        <label className="form-label">Morning ICA Count:</label>
                        <input
                            type="number"
                            className="form-control"
                            value={morningIcaCount}
                            min={2}
                            max={4}
                            onChange={(e) => setMorningIcaCount(e.target.value)}
                        />
                        </div>
                        <div className="col-md-3">
                        <label className="form-label">Afternoon ICA Count:</label>
                        <input
                            type="number"
                            className="form-control"
                            value={afternoonIcaCount}
                            min={2}
                            max={4}
                            onChange={(e) => setAfternoonIcaCount(e.target.value)}
                        />
                        </div>
                    <div className="col-md-2 d-grid">
                        <button className="btn btn-success mt-4" onClick={handleDownloadSchedule}>
                            Generate Schedule
                        </button>
                    </div>
                </div>
            </div>

            

            {/* Search Bar */}
            <div className="mb-3">
                <input
                    type="text"
                    className="form-control"
                    placeholder="Search instructors..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                />
            </div>

             {/* Worker Cards */}
             <div className="row g-2">
                {sortedWorkers
                    .filter((worker) => worker.name.toLowerCase().includes(searchQuery.toLowerCase()))
                    .map((worker) => {

                        let borderClass = "";
                        let statusBadge = null;
                        const todayRange = getTodayAvailability(worker.availability);

                        if (todayRange) {
                            borderClass = "border border-success";
                            statusBadge = <span className="badge bg-success ms-2">In Today</span>;
                        } else if (getNextAvailability(worker.availability)) {
                            borderClass = "border border-warning";
                            statusBadge = <span className="badge bg-warning text-dark ms-2">Available Soon</span>;
                        } else {
                            borderClass = "border border-secondary";
                            statusBadge = <span className="badge bg-secondary ms-2">No Availability</span>;
                        }


                        return (
                            <div className={`col-12 col-sm-6 col-md-4 col-lg-3 ${borderClass}`} key={worker.id}>
                                <div className="card h-100 shadow-sm">
                                    <div className="card-body p-2">
                                        <h6 className="card-title mb-2">
                                            {worker.name} {statusBadge}
                                        </h6>
                                        <p className="card-text mb-2">
                                            <strong>Roles:</strong> {worker.roles.join(", ")}
                                        </p>
                                        <p className="card-text mb-2">
                                        <strong>Availability:</strong> 
                                        {getAvailabilityStatus(worker.availability) === "today" && todayRange
                                            ? `${format(parseISO(todayRange.start), "hh:mm a")} - ${format(parseISO(todayRange.end), "hh:mm a")}`
                                            : getAvailabilityStatus(worker.availability) === "future"
                                            ? `Next: ${format(getNextAvailability(worker.availability), "MMM dd, yyyy HH:mm")}`
                                            : "No upcoming availability"}

                                        </p>
                                        <div className="d-flex justify-content-between">
                                            <button className="btn btn-primary btn-sm" onClick={() => navigate(`/update-worker/${worker.id}`)}>
                                                Update
                                            </button>
                                            <button className="btn btn-danger btn-sm" onClick={() => handleDelete(worker.id)}>
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
