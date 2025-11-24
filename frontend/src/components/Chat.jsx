/**
 * Chat Component: Main chat interface for text and audio interactions
 * 
 * This component manages:
 * - Chat message history (user and bot messages)
 * - Text input and sending
 * - Audio recording integration
 * - Displaying bot responses with policy suggestions and sources
 * - Loading states
 */

import React, { useState, useRef, useEffect } from 'react'
import AudioRecorder from './AudioRecorder'
import './Chat.css'

// API base URL (adjust if backend runs on different port)
const API_BASE_URL = 'http://localhost:8000'

function Chat() {
  // State for chat messages
  // Each message has: { from: 'user' | 'bot', type: 'text' | 'audio', text, audioUrl?, suggestions?, sources? }
  const [messages, setMessages] = useState([])
  
  // Loading state for API calls
  const [isLoading, setIsLoading] = useState(false)
  
  // Text input state
  const [inputText, setInputText] = useState('')
  
  // Reference to scroll to bottom of chat
  const messagesEndRef = useRef(null)
  
  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])
  
  /**
   * Handle sending a text message
   * 
   * Process:
   * 1. Add user message to chat
   * 2. Call backend API
   * 3. Add bot response to chat
   */
  const handleSendText = async (message) => {
    if (!message.trim()) return
    
    // Add user message to chat
    const userMessage = {
      from: 'user',
      type: 'text',
      text: message
    }
    setMessages(prev => [...prev, userMessage])
    setIsLoading(true)
    
    try {
      // Call backend text chat API
      const response = await fetch(`${API_BASE_URL}/api/chat-text`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: message,
          session_id: null, // Could implement session tracking
          policy_type: null, // Could extract from UI filters
          region: null
        })
      })
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Add bot response to chat
      const botMessage = {
        from: 'bot',
        type: 'text',
        text: data.answer,
        suggestions: data.policy_suggestions || [],
        sources: data.sources || []
      }
      setMessages(prev => [...prev, botMessage])
      
    } catch (error) {
      console.error('Error sending message:', error)
      // Add helpful error message to chat
      let errorText = 'I\'m having trouble processing your request right now. '
      if (error.message && error.message.includes('Failed to fetch')) {
        errorText += 'Please check if the backend server is running and try again.'
      } else if (error.message && error.message.includes('500')) {
        errorText += 'The server encountered an issue. Please try rephrasing your question or contact support.'
      } else {
        errorText += 'Please try again in a moment or rephrase your question.'
      }
      
      const errorMessage = {
        from: 'bot',
        type: 'text',
        text: errorText,
        suggestions: [],
        sources: []
      }
      setMessages(prev => [...prev, errorMessage])
    } finally {
      setIsLoading(false)
    }
  }
  
  /**
   * Handle audio response from AudioRecorder component
   * 
   * This is called when audio recording is processed and
   * the backend returns a response with transcript and TTS audio.
   */
  const handleAudioResponse = (response) => {
    // Add user transcript as a message
    const userMessage = {
      from: 'user',
      type: 'audio',
      text: response.transcript
    }
    
    // Add bot response with audio
    const botMessage = {
      from: 'bot',
      type: 'audio',
      text: response.answer,
      audioUrl: `${API_BASE_URL}${response.audio_url}`,
      suggestions: response.policy_suggestions || [],
      sources: response.sources || []
    }
    
    setMessages(prev => [...prev, userMessage, botMessage])
  }
  
  /**
   * Handle form submission for text input
   */
  const handleSubmit = (e) => {
    e.preventDefault()
    if (inputText.trim() && !isLoading) {
      handleSendText(inputText)
      setInputText('')
    }
  }
  
  return (
    <div className="chat-container">
      {/* Chat messages area */}
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="welcome-message">
            <p>👋 Welcome to the Insurance Chatbot!</p>
            <p>Ask me questions about health, car, or bike insurance policies.</p>
            <p>You can type your question or use the microphone to speak.</p>
          </div>
        )}
        
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.from}`}>
            <div className="message-bubble">
              <div className="message-text">{message.text}</div>
              
              {/* Audio playback for bot audio messages */}
              {message.from === 'bot' && message.type === 'audio' && message.audioUrl && (
                <div className="audio-player">
                  <audio controls src={message.audioUrl}>
                    Your browser does not support audio playback.
                  </audio>
                </div>
              )}
              
              {/* Policy suggestions */}
              {message.suggestions && message.suggestions.length > 0 && (
                <div className="suggestions">
                  <h4>Recommended Policies:</h4>
                  <ul>
                    {message.suggestions.map((suggestion, idx) => {
                      // Extract website URL from reason if present
                      const urlMatch = suggestion.reason.match(/https?:\/\/[^\s]+/);
                      const websiteUrl = urlMatch ? urlMatch[0] : null;
                      const reasonText = websiteUrl 
                        ? suggestion.reason.replace(websiteUrl, '').trim()
                        : suggestion.reason;
                      
                      return (
                        <li key={idx}>
                          <strong>{suggestion.title}</strong> ({suggestion.policy_type})
                          <br />
                          <small>{reasonText}</small>
                          {websiteUrl && (
                            <div className="website-link">
                              <a href={websiteUrl} target="_blank" rel="noopener noreferrer">
                                Visit Website →
                              </a>
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                </div>
              )}
              
              {/* Sources */}
              {message.sources && message.sources.length > 0 && (
                <details className="sources">
                  <summary>View Sources ({message.sources.length})</summary>
                  <div className="sources-list">
                    {message.sources.map((source, idx) => (
                      <div key={idx} className="source-item">
                        <strong>{source.policy_id}</strong> ({source.policy_type}) - {source.clause_type}
                        <p>{source.text_snippet}</p>
                      </div>
                    ))}
                  </div>
                </details>
              )}
            </div>
          </div>
        ))}
        
        {/* Loading indicator */}
        {isLoading && (
          <div className="message bot">
            <div className="message-bubble">
              <div className="loading-spinner">
                <div className="spinner"></div>
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}
        
        <div ref={messagesEndRef} />
      </div>
      
      {/* Input area */}
      <div className="chat-input-area">
        <form onSubmit={handleSubmit} className="input-form">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your question here..."
            disabled={isLoading}
            className="text-input"
          />
          <button
            type="submit"
            disabled={isLoading || !inputText.trim()}
            className="send-button"
          >
            Send
          </button>
        </form>
        
        {/* Audio recorder component */}
        <div className="audio-recorder-container">
          <AudioRecorder
            onResponse={handleAudioResponse}
            disabled={isLoading}
          />
        </div>
      </div>
    </div>
  )
}

export default Chat

