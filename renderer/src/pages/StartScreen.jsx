import React from "react";

export default function StartScreen({ onStart }) {
  return (
    <div className="start-screen">
      <h1>Director of Rugby</h1>
      <p>Welcome! Start a new game to begin your journey.</p>
      <button onClick={onStart}> Start New Game</button>
    </div>
  );
}
