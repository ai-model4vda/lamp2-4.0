import React, { useState, useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import "./App.css";

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [stage, setStage] = useState("initial");
  const [userDetails, setUserDetails] = useState("");
  const [selectedModel, setSelectedModel] = useState("llama-3.3-70b-versatile");
  const [isRagEnabled, setIsRagEnabled] = useState(true);
  const hasSentInitialMessages = useRef(false);

  const initialMessages = [
    {
      type: "received",
      text: "**LAMP² 4.0 – Legal Analytics Model for Prediction and Prescription**  \n\nLAMP² 4.0 (Legal Analytics, Modeling, Prediction, and Prescription) is an AI-powered legal analytics and prediction model designed to assist victims of domestic abuse. It leverages predictive algorithms and prescriptive analytics to analyze legal issues, derive insights from past judgments, and recommend actionable solutions. Engineered for accessibility, it integrates emotional intelligence with legal expertise to provide a secure, user-centric platform for timely assistance and empowerment.",
    },
    {
      type: "received",
      text: "Welcome to LAMP² 4.0, a safe space for victims of domestic abuse. I’m here to listen, support, and guide you with care and confidentiality.",
    },
    {
      type: "received",
      text: "To get started, could you please tell me your name and age?",
    },
  ];

  useEffect(() => {
    if (!hasSentInitialMessages.current) {
      const sendInitialMessages = async () => {
        for (const message of initialMessages) {
          await new Promise((resolve) => setTimeout(resolve, 1000));
          setMessages((prev) => [...prev, message]);
        }
      };
      sendInitialMessages();
      hasSentInitialMessages.current = true;
    }
  }, []);

  const models = [
    "llama-3.3-70b-versatile",
    "llama3-8b-8192",
    "llama3-70b-8192",
    "llama-3.1-8b-instant",
    "mixtral-8x7b-32768",
  ];

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { type: "sent", text: input };
    setMessages((prev) => [...prev, userMessage]);

    if (stage === "initial") {
      setUserDetails(input.trim());
      setMessages((prev) => [
        ...prev,
        {
          type: "received",
          text: "Thank you! Could you now describe your case?",
        },
      ]);
      setStage("case-description");
      setInput("");
      return;
    }

    if (stage === "case-description") {
      const finalInput = `${userDetails}, Case Description: ${input.trim()}`;
      setStage("final");
      setInput("");

      try {
        const url = isRagEnabled
          ? "http://127.0.0.1:5000/getresult"
          : "http://127.0.0.1:5000/getresultwithoutrag";
        const requestBody = {
          request: {
            "current message": finalInput,
            model: selectedModel,
            History: [],
          },
        };

        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        });

        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { type: "received", text: data.result },
        ]);
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          { type: "received", text: "Error: Unable to connect to the server." },
        ]);
      }
      return;
    }

    if (stage === "final") {
      setInput("");
      const chatHistory = messages
        .slice(initialMessages.length)
        .map((msg) => ({
          role: msg.type === "sent" ? "user" : "assistant",
          content: msg.text,
        }));

      try {
        const url = isRagEnabled
          ? "http://127.0.0.1:5000/getresult"
          : "http://127.0.0.1:5000/getresultwithoutrag";
        const requestBody = {
          request: {
            "current message": input,
            model: selectedModel,
            History: chatHistory,
          },
        };

        const response = await fetch(url, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(requestBody),
        });

        const data = await response.json();
        setMessages((prev) => [
          ...prev,
          { type: "received", text: data.result },
        ]);
      } catch (error) {
        setMessages((prev) => [
          ...prev,
          { type: "received", text: "Error: Unable to connect to the server." },
        ]);
      }
      return;
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === "Enter") {
      sendMessage();
    }
  };

  const toggleRag = () => {
    setIsRagEnabled((prev) => !prev);
  };

  return (
    <div className="app">
      <div className="chat-window">
        <header className="chat-header">
          <div className="model-select">
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
            >
              {models.map((model, index) => (
                <option key={index} value={model}>
                  {model}
                </option>
              ))}
            </select>
          </div>
          <h1>LAMP² 4.0</h1>
          <div className="rag-toggle-container">
            <label className="switch">
              <input
                type="checkbox"
                checked={isRagEnabled}
                onChange={toggleRag}
              />
              <span className="slider"></span>
            </label>
            <span>{isRagEnabled ? "RAG: ON" : "RAG: OFF"}</span>
          </div>
        </header>
        <div className="chat-messages">
          {messages.map((msg, index) => (
            <div key={index} className={`message ${msg.type}`}>
              <span
                className={`message-type ${
                  msg.type === "sent" ? "sent-message" : "received-message"
                }`}
              >
                {msg.type === "sent" ? "You" : "Chatbot"}
              </span>
              <div className="message-content">
                <ReactMarkdown>{msg.text}</ReactMarkdown>
              </div>
            </div>
          ))}
        </div>

        <footer className="chat-footer">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message..."
          />
          <button onClick={sendMessage}>Send</button>
        </footer>
      </div>
    </div>
  );
}

export default App;
