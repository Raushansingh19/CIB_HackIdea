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
  
  // Session ID for conversation continuity
  const [sessionId, setSessionId] = useState(null)
  
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
          session_id: sessionId, // Use stored session ID for conversation continuity
          policy_type: null, // Could extract from UI filters
          region: null
        })
      })
      
      if (!response.ok) {
        throw new Error(`API error: ${response.status}`)
      }
      
      const data = await response.json()
      
      // Store session ID for conversation continuity
      if (data.session_id && !sessionId) {
        setSessionId(data.session_id)
      }
      
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
      
      // Provide helpful response based on error type
      let errorText = ''
      if (error.message && error.message.includes('Failed to fetch')) {
        // Backend not reachable - provide helpful guidance
        errorText = `I'm having trouble connecting to the server right now. 

Please check:
• Is the backend server running? (Should be on http://localhost:8000)
• Try refreshing the page

In the meantime, I can help you with:
• **Health Insurance**: Coverage for hospitalization, pre-existing conditions, age-specific plans
• **Car Insurance**: Liability, collision, comprehensive coverage options
• **Bike Insurance**: Motorcycle and bicycle coverage options

Once the connection is restored, feel free to ask me specific questions!`
      } else if (error.message && error.message.includes('500')) {
        // Server error - provide helpful guidance
        errorText = `I encountered an issue processing your request. 

Let me help you with insurance information:

• **Health Insurance**: For questions about coverage, premiums, waiting periods, or age-specific plans
• **Car Insurance**: For questions about liability limits, deductibles, or optional coverage
• **Bike Insurance**: For questions about motorcycle or bicycle coverage

Please try rephrasing your question, or ask about a specific insurance type!`
      } else {
        // Other errors - provide general helpful response
        errorText = `I'd be happy to help you with insurance questions!

Here's what I can assist with:
• **Health Insurance**: Coverage options, eligibility, waiting periods, age considerations
• **Car Insurance**: Coverage types, liability limits, deductibles, optional features
• **Bike Insurance**: Motorcycle and bicycle coverage, theft protection, liability

What type of insurance are you interested in?`
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
    console.log('Audio response received:', response)
    
    // Store session ID if provided
    if (response.session_id && !sessionId) {
      setSessionId(response.session_id)
    }
    
    // Add user transcript as a message (show what was transcribed)
    if (response.transcript && response.transcript.trim()) {
      const userMessage = {
        from: 'user',
        type: 'audio',
        text: response.transcript
      }
      setMessages(prev => [...prev, userMessage])
    }
    
    // Add bot response with audio
    const botMessage = {
      from: 'bot',
      type: 'audio',
      text: response.answer || 'I received your audio message.',
      audioUrl: response.audio_url ? `${API_BASE_URL}${response.audio_url}` : null,
      suggestions: response.policy_suggestions || [],
      sources: response.sources || []
    }
    
    setMessages(prev => [...prev, botMessage])
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

