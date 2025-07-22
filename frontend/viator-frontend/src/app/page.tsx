"use client";

import { useState, useRef, useEffect } from "react";
import FlightsTable from "@/components/flights";
import { json } from "stream/consumers";

type Message = {
  role: "user" | "assistant";
  content: string;
  flightsData?: any;
};

export default function Home() {
  const [input, setInput] = useState("");
  const [response, setResponse] = useState("");
  const [parsedResponse, setParsedResponse] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [conversation, setConversation] = useState<Message[]>([]);
  const controllerRef = useRef<AbortController | null>(null);

  // useEffect(() => {
  //   console.log(conversation)
  // }, [conversation]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setResponse("");
    setParsedResponse("");

    // Add user message
    setConversation(prev => [...prev, { role: "user", content: input}]);

    controllerRef.current = new AbortController();

    const res = await fetch("http://localhost:8000/chat", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ input }),
      signal: controllerRef.current.signal,
    });

    if (!res.body) {
      setIsLoading(false);
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder("utf-8");

    let done = false;
    let assistantMessage = "";
    let toolUsed = "";
    let flightData = null;
    while (!done) {
      const { value, done: streamDone } = await reader.read();
      done = streamDone;
      const text = decoder.decode(value);
      
      console.log("text", text)
      const split_text = text.trim().split("[END]")
      split_text.pop()
      console.log("split", split_text)
      
      for (const chunk of split_text) {
        const jsonChunk = JSON.parse(chunk);
        console.log("json", jsonChunk)
        if (jsonChunk?.type === "tool") {
          toolUsed = jsonChunk.tool_name;
          assistantMessage += `\nUsing tool: ${toolUsed}\n`;
        } else if (jsonChunk?.type === "flight_response") {
          assistantMessage += `\n${jsonChunk.message}\n`;
          flightData = jsonChunk.flights_data;
        } else if (jsonChunk?.type === "stream") {
          assistantMessage += jsonChunk.content;
          // Stream the update into the conversation immediately
          setConversation(prev => {
            const last = prev[prev.length - 1];
            if (last?.role === "assistant") {
              return [...prev.slice(0, -1), { ...last, content: assistantMessage }];
            } else {
              return [...prev, { role: "assistant", content: assistantMessage }];
            }
          });
        }
      }
    }

    // ✅ Append full assistant message + any flight data just once
    setConversation(prev => {
      const last = prev[prev.length - 1];
      const newMessage = {
      role: "assistant" as const,
      content: assistantMessage.trim(),
      ...(flightData ? { flightsData: flightData } : {})
    };

      if (last?.role === "assistant") {
        return [...prev.slice(0, -1), newMessage];
      } else {
        return [...prev, newMessage];
      }
    });

    setIsLoading(false);
  };

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-900">
      <h1 className="text-2xl font-bold mb-4 text-white">Travel AI Chat</h1>

      <form onSubmit={handleSubmit} className="w-full max-w-xl flex gap-2">
        <input
          type="text"
          value={input}
          onChange={e => setInput(e.target.value)}
          className="flex-grow p-2 border border-gray-700 rounded bg-gray-800 text-white"
          placeholder="Ask about your next trip..."
        />
        <button
          type="submit"
          disabled={isLoading}
          className="px-4 py-2 bg-blue-600 text-white rounded"
        >
          {isLoading ? "Loading..." : "Send"}
        </button>
      </form>

      <div className="w-full max-w-xl mt-6 bg-gray-800 p-4 rounded shadow">
        <h2 className="font-semibold mb-2 text-white">Conversation History:</h2>
        <div className="space-y-2 text-sm text-gray-300">
          {conversation.map((msg, idx) => (
            <div key={idx} className="mb-4">
              <div>
                <span className="font-bold text-blue-400">
                  {msg.role === "user" ? "You" : "AI"}:
                </span>{" "}
                <span className="whitespace-pre-wrap">{msg.content}</span>
              </div>

              {msg.flightsData && (
                <div className="mt-2">
                  <FlightsTable flightsData={msg.flightsData} />
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {parsedResponse && (
        <div className="w-full max-w-xl mt-4 bg-gray-800 p-4 rounded shadow">
          <h2 className="font-semibold mb-2 text-white">Parsed Response:</h2>
          <pre className="whitespace-pre-wrap text-sm text-gray-200">
            {parsedResponse}
          </pre>
        </div>
      )}
    </div>
  );
}




// "use client";

// import { useState, useRef, useEffect } from "react";
// import FlightsTable from "@/components/flights";

// export default function Home() {
//   const [input, setInput] = useState("");
//   const [response, setResponse] = useState("");
//   const [parsedResponse, setParsedResponse] = useState("");
//   const [flightsData, setFlightsData] = useState<any>(null); // New state
//   const [isLoading, setIsLoading] = useState(false);
//   const controllerRef = useRef<AbortController | null>(null);

//   useEffect(() => {
//   try {
//     const json = JSON.parse(response);
//     if (json.message) {
//       setParsedResponse(json.message);
//     }
//     if (json.flights_data) {
//       setFlightsData(json.flights_data);
//     }
//   } catch (e) {
//     // It's not a complete JSON yet, wait for more data
//   }
// }, [response]);

//   const handleSubmit = async (e: React.FormEvent) => {
//     e.preventDefault();
//     setIsLoading(true);
//     setResponse("");
//     setParsedResponse("");
//     setFlightsData(null); // Reset previous data

//     controllerRef.current = new AbortController();

//     const res = await fetch("http://localhost:8000/chat", {
//       method: "POST",
//       headers: {
//         "Content-Type": "application/json",
//       },
//       body: JSON.stringify({ input }),
//       signal: controllerRef.current.signal,
//     });

//     if (!res.body) {
//       setIsLoading(false);
//       return;
//     }

//     const reader = res.body.getReader();
//     const decoder = new TextDecoder("utf-8");

//     let done = false;
//     while (!done) {
//       const { value, done: readerDone } = await reader.read();
//       done = readerDone;
//       const chunk = decoder.decode(value);
//       setResponse(prev => prev + chunk);
//       console.log(response)
//     }
//     setIsLoading(false);
//   };

//   return (
//     <div className="min-h-screen flex flex-col items-center justify-center p-8 bg-gray-900">
//       <h1 className="text-2xl font-bold mb-4 text-white">Travel AI Chat</h1>
//       <form onSubmit={handleSubmit} className="w-full max-w-xl flex gap-2">
//         <input
//           type="text"
//           value={input}
//           onChange={e => setInput(e.target.value)}
//           className="flex-grow p-2 border border-gray-700 rounded bg-gray-800 text-white"
//           placeholder="Ask about your next trip..."
//         />
//         <button
//           type="submit"
//           disabled={isLoading}
//           className="px-4 py-2 bg-blue-600 text-white rounded"
//         >
//           {isLoading ? "Loading..." : "Send"}
//         </button>
//       </form>

//       <div className="w-full max-w-xl mt-6 bg-gray-800 p-4 rounded shadow">
//         <h2 className="font-semibold mb-2 text-white">Parsed Response:</h2>
//         <pre className="whitespace-pre-wrap text-sm text-gray-200">
//           {parsedResponse}
//         </pre>
//         <h2 className="font-semibold mb-2 text-white">Assistant Response:</h2>
//         <pre className="whitespace-pre-wrap text-sm text-gray-200">
//           {response}
//         </pre>
//       </div>

//       {flightsData && (
//         <FlightsTable flightsData={flightsData} />
//       )}
//     </div>
//   );
// }
