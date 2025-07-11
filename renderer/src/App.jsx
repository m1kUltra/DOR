import React, { useState } from "react";
import StartScreen from "./pages/StartScreen";
import GameShell from "./GameShell"; // The actual game UI lives here

import "./App.css";

export default function App() {
  const [hasGameStarted, setHasGameStarted] = useState(false);

  if (!hasGameStarted) {
    return <StartScreen onStart={() => setHasGameStarted(true)} />;
  }

  return <GameShell />;
}
