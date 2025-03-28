import React from "react";
import { BrowserRouter as Router, Routes, Route, useLocation, useNavigate, Link } from "react-router-dom";

import LoginPage from './components/LoginPage';
import WorkerList from "./components/WorkerList";
import CreateWorker from "./components/CreateWorker";
import UpdateWorker from "./components/UpdateWorker";
import ProtectedRoute from "./components/ProtectedRoute";


// 🔹 Navbar Component with Logout Button
const Navbar = () => {
    const location = useLocation();
    const navigate = useNavigate();

    // Hide navbar on login page
    if (location.pathname === "/") return null;

    const handleLogout = () => {
        localStorage.removeItem("isAuthenticated");
        navigate("/");
    };

    return (
        <nav className="navbar navbar-expand-lg navbar-light bg-light">
            <div className="container-fluid d-flex justify-content-between">
                <div className="d-flex">
                    <Link className="navbar-brand" to="/workers">Day Planner</Link>
                    <ul className="navbar-nav ms-3">
                        <li className="nav-item">
                            <Link className="nav-link" to="/create-worker">Create Worker</Link>
                        </li>
                    </ul>
                </div>
                <button
                    className="btn btn-outline-danger"
                    onClick={() => {
                        localStorage.removeItem("isAuthenticated");
                        window.location.href = "/";
                    }}
                >
                    Logout
                </button>
            </div>
        </nav>
    );
};

const App = () => {
    return (
        <Router>
            <Navbar />
            <div className="container mt-4">
                <Routes>
                    <Route path="/" element={<LoginPage />} />
                    <Route path="/workers" element={<ProtectedRoute><WorkerList /></ProtectedRoute>} />
                    <Route path="/create-worker" element={<ProtectedRoute><CreateWorker /></ProtectedRoute>} />
                    <Route path="/update-worker/:id" element={<ProtectedRoute><UpdateWorker /></ProtectedRoute>} />
                </Routes>
            </div>
        </Router>
    );
};

export default App;

