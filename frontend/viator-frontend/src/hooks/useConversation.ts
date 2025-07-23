import { useState } from "react";
type Message = {
  role: "user" | "assistant";
  content: string;
  toolsUsed?: string[];
  flightsData?: any; // JSON result of Flight Search API
  itineraryData?: any; // JSON result of structured itinerary
};

export function useConversation() {
    const [conversation, setConversation] = useState<Message[]>([]);

    function addUserMessage(message: string) {
        setConversation(prev => [...prev, { role: "user", content: message }]);
    }

    // Stream into the conversation as messages arrive
    function updateAssistantStream(content: any) {
        setConversation(prev => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant") {
                return [...prev.slice(0, -1), { ...last, content }];
            } else {
                return [...prev, { role: "assistant", content }];
            }
        });
    }

    // Add final assistant message once stream completes
    function finalizeAssistantMessage(content: string, toolsUsed?: string[], flightsData?: any, itineraryData?: any) {
        setConversation(prev => {
            const last = prev[prev.length - 1];
            const message = {
                role: "assistant" as const,
                content: content.trim(),
                ...(flightsData ? { flightsData } : {}),
                ...(itineraryData ? { itineraryData } : {}),
                ...(toolsUsed ? { toolsUsed } : [])
            };
            if (last?.role === "assistant") {
                return [...prev.slice(0, -1), message];
            } else {
                return [...prev, message];
            }
        });
    }
    return {
        conversation,
        setConversation,
        addUserMessage,
        updateAssistantStream,
        finalizeAssistantMessage,
    };
}