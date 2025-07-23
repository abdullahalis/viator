"use client";

import { useState, useRef, useEffect } from "react";
import FlightsTable from "@/components/flights";
import ItineraryTable from "@/components/itinerary";
import ChatMessage from "@/components/ChatMessage"
import InputForm from "@/components/InputForm";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import Markdown from 'markdown-to-jsx';
import { handleStreamedResponse } from "@/lib/streamHandlers";
import { useConversation } from "@/hooks/useConversation";
import { apiCaller } from "@/lib/api"

export default function Home() {
  const {
  conversation,
  setConversation,
  addUserMessage,
  updateAssistantStream,
  finalizeAssistantMessage,
} = useConversation();

  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const controllerRef = useRef<AbortController | null>(null);  // Handle DOM errors
  const bottomRef = useRef<HTMLDivElement | null>(null); // Automatic Scrolling

  useEffect(() => {
    const timeout = setTimeout(() => {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
    return () => clearTimeout(timeout)
  }, [conversation]);

  async function sendMessage(message: string) {
    setIsLoading(true);
    setInput("");
    
    // Ignore empty messages
    if (!message.trim()) {
      setIsLoading(false);
      return;
    }
    setError(null);
    addUserMessage(message);
   
    controllerRef.current = new AbortController();

    try {
      const res = await apiCaller({
        url: "http://localhost:8000/chat",
        input: message,
        signal: controllerRef.current
      })

      await handleStreamedResponse({
        res,
        updateAssistantStream,
        finalizeAssistantMessage,
        setError,
      });
    } catch (err: any) {
      console.error("Fetch error:", err);
      setError(err.message || "Something went wrong. Please try again.");
    } finally {
      setIsLoading(false);
    }
    
  }

  const handleSubmit = async (e?: React.FormEvent, overrideInput?: string) => {
    if (e) e.preventDefault();
    const message = overrideInput ?? input;
    sendMessage(message)
  };

  const handleInitialMessage = () => {
    const initialInput = "Hi! What do you do?";
    setInput(initialInput);
    sendMessage(initialInput);
  };

  function handleStop() {
    if (controllerRef.current) {
      controllerRef.current.abort();
      controllerRef.current = null;
      setIsLoading(false);
      setError("Request was manually stopped.");
    }
}

  return (
  <div className="h-screen w-full flex flex-col bg-secondary text-white relative">
    {/* Title */}
    <div className="p-6 text-center  bg-secondary">
      <h1 className="text-2xl font-bold">Viator - AI Travel Agent</h1>
    </div>

    {/* Chat Container */}
    <Card className="flex-1 overflow-y-auto bg-background shadow-inner">
      <CardContent className="p-6 space-y-4">
        {/* Learn More Button */}
        {conversation.length === 0 && (
          <div className="flex justify-center items-center h-full mt-10">
            <Button
              onClick={handleInitialMessage}
              className="bg-transparent border border-black text-black font-semibold hover:bg-primary hover:text-white hover:border-transparent cursor-pointer"
            >
              Learn more about what I can do!
            </Button>
          </div>
        )}

        {conversation.map((msg, idx) => (
          <div key={idx} className="mb-4 w-full">
            <ChatMessage msg={msg} />
          </div>
        ))}
        <div ref={bottomRef} />
      </CardContent>
    </Card>

    {/* Floating Input */}
    <InputForm input={input} setInput={setInput} isLoading={isLoading} handleSubmit={handleSubmit} handleStop={handleStop}/>

    {/* Loading Symbol */}
    {isLoading && (
        <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-6 border-4 border-gray-400 border-t-transparent rounded-full animate-spin" />
    )}

    {/* Error Message */}
    {error && (
      <div className="absolute bottom-40 left-1/2 -translate-x-1/2 bg-red-100 text-red-800 px-4 py-2 rounded shadow max-w-[90%] text-sm">
        {error}
      </div>
    )}
  </div>
);
}