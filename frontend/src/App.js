import React from "react";
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";
import WorkerList from "./components/WorkerList";
import CreateWorker from "./components/CreateWorker";
import UpdateWorker from "./components/UpdateWorker";

const App = () => {
    return (
        <Router>
            <nav className="navbar navbar-expand-lg navbar-light bg-light">
                <div className="container-fluid">
                    <a className="navbar-brand" href="/">Day Planner</a>
                    <div className="collapse navbar-collapse">
                        <ul className="navbar-nav">
                            
                            <li className="nav-item">
                                <Link className="nav-link" to="/create-worker">Create Worker</Link>
                            </li>
                        </ul>
                    </div>
                </div>
            </nav>
            <div className="container mt-4">
                <Routes>
                    <Route path="/" element={<WorkerList />} />
                    <Route path="/create-worker" element={<CreateWorker />} />
                    <Route path="/update-worker/:id" element={<UpdateWorker />} />
                </Routes>
            </div>
        </Router>
    );
};

export default App;
