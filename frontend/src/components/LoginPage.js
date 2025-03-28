import React, { useState } from "react";
import { useNavigate } from "react-router-dom"; 
import "../css/login.css";

const LoginPage = () => {
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");
    const navigate = useNavigate(); 

    const handleSubmit = (e) => {
        e.preventDefault();
        if (password === "CenterParcs") {
            localStorage.setItem("isAuthenticated", "true");
            navigate("/workers");
        } else {
            setError("Incorrect password. Try again.");
        }
    };    

    return (
        <div className="login-container">
            <form onSubmit={handleSubmit} autoComplete="off">
                <h2>Login</h2>
                <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Enter Password"
                    autoComplete="new-password" 
                />
                {error && <p className="error">{error}</p>}
                <button type="submit">Login</button>
            </form>
        </div>
    );
};

export default LoginPage;
