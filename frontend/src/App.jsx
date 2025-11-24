/**
 * Main App Component for Insurance Chatbot
 * 
 * This component serves as the root of the application and renders
 * the Chat component which handles all user interactions.
 */

import React from 'react'
import Chat from './components/Chat'
import './App.css'

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Insurance Chatbot</h1>
        <p>Ask questions about your insurance policies</p>
      </header>
      <Chat />
    </div>
  )
}

export default App

