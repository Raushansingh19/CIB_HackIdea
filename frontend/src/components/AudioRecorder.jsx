/**
 * AudioRecorder Component: Handles audio recording and playback
 * 
 * This component:
 * - Uses browser MediaRecorder API to record audio
 * - Sends recorded audio to backend for STT processing
 * - Displays recording state and handles playback of TTS response
 * 
 * Browser APIs used:
 * - navigator.mediaDevices.getUserMedia(): Request microphone access
 * - MediaRecorder: Record audio from microphone
 * - Blob/File API: Handle audio data
 */

import React, { useState, useRef } from 'react'
import './AudioRecorder.css'

// API base URL
const API_BASE_URL = 'http://localhost:8000'

function AudioRecorder({ onResponse, disabled }) {
  // Recording state
  const [isRecording, setIsRecording] = useState(false)
  const [isProcessing, setIsProcessing] = useState(false)
  
  // Refs for MediaRecorder and audio stream
  const mediaRecorderRef = useRef(null)
  const audioChunksRef = useRef([])
  const streamRef = useRef(null)
  
  /**
   * Start recording audio from microphone
   * 
   * Process:
   * 1. Request microphone access
   * 2. Create MediaRecorder instance
   * 3. Start recording and collect audio chunks
   */
  const startRecording = async () => {
    try {
      // Request microphone access
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      
      // Create MediaRecorder
      // Use 'audio/webm' for Chrome/Firefox, fallback to 'audio/mp4' for Safari
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') 
        ? 'audio/webm' 
        : MediaRecorder.isTypeSupported('audio/mp4')
        ? 'audio/mp4'
        : ''
      
      const options = mimeType ? { mimeType: mimeType } : {}
      const mediaRecorder = new MediaRecorder(stream, options)
      mediaRecorderRef.current = mediaRecorder
      audioChunksRef.current = []
      
      // Collect audio chunks as they're recorded
      mediaRecorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data)
          console.log(`Received audio chunk: ${event.data.size} bytes`)
        }
      }
      
      // Handle errors
      mediaRecorder.onerror = (event) => {
        console.error('MediaRecorder error:', event.error)
        setIsRecording(false)
        alert('Recording error occurred. Please try again.')
      }
      
      // Start recording with timeslice to get regular data chunks
      // This ensures we get data even if stop() is called quickly
      mediaRecorder.start(1000) // Get chunks every 1 second
      setIsRecording(true)
      
      console.log('Recording started with mimeType:', mimeType || 'default')
      
    } catch (error) {
      console.error('Error accessing microphone:', error)
      alert('Could not access microphone. Please check permissions.')
    }
  }
  
  /**
   * Stop recording and send audio to backend
   * 
   * Process:
   * 1. Stop MediaRecorder
   * 2. Stop audio stream
   * 3. Create Blob from audio chunks
   * 4. Send to backend API
   * 5. Call onResponse callback with result
   */
  const stopRecording = async () => {
    if (!mediaRecorderRef.current || !isRecording) {
      console.log('Cannot stop: not recording or MediaRecorder not available')
      return
    }
    
    const mediaRecorder = mediaRecorderRef.current
    const stream = streamRef.current
    
    // Immediately update UI state
    setIsRecording(false)
    setIsProcessing(true)
    
    return new Promise((resolve) => {
      // Set up the onstop handler BEFORE stopping
      mediaRecorder.onstop = async () => {
        console.log('MediaRecorder stopped, processing audio...')
        
        // Stop the audio stream tracks
        if (stream) {
          stream.getTracks().forEach(track => {
            track.stop()
            console.log('Stopped audio track:', track.kind)
          })
          streamRef.current = null
        }
        
        // Create Blob from audio chunks
        const mimeType = mediaRecorder.mimeType || 'audio/webm'
        const audioBlob = new Blob(audioChunksRef.current, { 
          type: mimeType
        })
        
        console.log(`Created audio blob: ${audioBlob.size} bytes, type: ${mimeType}`)
        
        // Clear the chunks for next recording
        audioChunksRef.current = []
        
        try {
          // Send audio to backend
          const formData = new FormData()
          const fileName = mimeType.includes('webm') ? 'recording.webm' : 'recording.mp4'
          formData.append('audio_file', audioBlob, fileName)
          
          console.log('Sending audio to backend...')
          
          const response = await fetch(`${API_BASE_URL}/api/chat-audio`, {
            method: 'POST',
            body: formData
          })
          
          if (!response.ok) {
            const errorText = await response.text()
            throw new Error(`API error: ${response.status} - ${errorText}`)
          }
          
          const data = await response.json()
          console.log('Received response from backend')
          
          // Call parent callback with response
          if (onResponse) {
            onResponse(data)
          }
          
        } catch (error) {
          console.error('Error sending audio:', error)
          alert(`Error processing audio: ${error.message}. Please try again.`)
        } finally {
          setIsProcessing(false)
          mediaRecorderRef.current = null
          resolve()
        }
      }
      
      // Request any remaining data before stopping
      if (mediaRecorder.state === 'recording') {
        try {
          mediaRecorder.requestData()
          // Small delay to ensure data is collected
          setTimeout(() => {
            if (mediaRecorder.state === 'recording') {
              console.log('Stopping MediaRecorder...')
              mediaRecorder.stop()
            }
          }, 100)
        } catch (error) {
          console.error('Error requesting data:', error)
          // Try to stop anyway
          if (mediaRecorder.state === 'recording') {
            mediaRecorder.stop()
          }
        }
      } else {
        console.log('MediaRecorder not in recording state:', mediaRecorder.state)
        setIsProcessing(false)
        resolve()
      }
    })
  }
  
  /**
   * Toggle recording (start/stop)
   */
  const toggleRecording = () => {
    if (disabled || isProcessing) return
    
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }
  
  return (
    <div className="audio-recorder">
      <button
        className={`record-button ${isRecording ? 'recording' : ''} ${isProcessing ? 'processing' : ''}`}
        onClick={toggleRecording}
        disabled={disabled || isProcessing}
        title={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isProcessing ? (
          <>
            <span className="spinner-small"></span>
            Processing...
          </>
        ) : isRecording ? (
          <>
            <span className="record-icon recording">●</span>
            Stop Recording
          </>
        ) : (
          <>
            <span className="record-icon">🎤</span>
            Record Audio
          </>
        )}
      </button>
      
      {isRecording && (
        <div className="recording-indicator">
          <span className="pulse"></span>
          Recording...
        </div>
      )}
    </div>
  )
}

export default AudioRecorder

