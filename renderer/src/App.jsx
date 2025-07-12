import React, { useState } from "react";
import StartScreen from "./pages/StartScreen";
import NewGame from "./pages/NewGame";
import GameShell from "./GameShell";

import "./App.css";

export default function App() {
  const [screen, setScreen] = useState("start"); // start | newgame | game

  if (screen === "start") {
    return <StartScreen onStart={() => setScreen("newgame")} />;
  }

  if (screen === "newgame") {
    return <NewGame onLaunchGame={() => setScreen("game")} />;
  }

  return <GameShell />;
}
