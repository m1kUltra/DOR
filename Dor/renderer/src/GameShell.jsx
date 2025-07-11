// src/GameShell.jsx
import React, { useState } from "react";
import Sidebar from "./components/Sidebar";
import TopBar from "./components/TopBar";

import Dashboard from "./pages/Dashboard";
import SquadView from "./pages/SquadView";
import FixturesCalendar from "./pages/FixturesCalendar";
import MatchSim from "./pages/MatchSim";
import Tactics from "./pages/Tactics";
import RecruitmentHub from "./pages/RecruitmentHub";
import Editor from "./pages/Editor.jsx";

export default function GameShell() {
  const [currentScreen, setCurrentScreen] = useState("dashboard");

  const renderScreen = () => {
    switch (currentScreen) {
      case "dashboard":
        return <Dashboard />;
      case "squad":
        return <SquadView />;
      case "fixtures":
        return <FixturesCalendar />;
      case "match":
        return <MatchSim />;
      case "tactics":
        return <Tactics />;
      case "transfers":
        return <RecruitmentHub />;
      case "editor": // 
        return <Editor />;
      default:
        return <Dashboard />;
    }
  };

  return (
    <div className="app-container">
      <Sidebar onNavigate={setCurrentScreen} />
      <div className="main-panel">
        <TopBar />
        <div className="screen-container">{renderScreen()}</div>
      </div>
    </div>
  );
}
