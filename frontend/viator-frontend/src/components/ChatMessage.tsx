import FlightsTable from "./flights";
import ItineraryTable from "./itinerary";
import Markdown from "markdown-to-jsx";

export default function ChatBubble({ msg }: { msg: any }) {
  if (msg.role === "user") {
    return (
      <div className="flex justify-end">
        <div className="bg-primary text-white px-4 py-2 rounded-xl max-w-xs text-right">
          {msg.content}
        </div>
      </div>
    );
  }

  return (
    <div className="p-4 pb-24 rounded-xl text-gray-800 overflow-y-auto max-h-[calc(100vh-200px)]">
      {msg.toolsUsed && (
        <div className="flex flex-col items-start mb-2">
          {msg.toolsUsed.map((tool: string, i: number) => (
            <div
              key={i}
              className="bg-accent text-white px-3 py-1 rounded-lg text-xs mb-1"
            >
              Used tool: {tool}
            </div>
          ))}
        </div>
      )}
      <Markdown className="whitespace-pre-wrap">{msg.content}</Markdown>

      {msg.flightsData && (
        <div className="mt-2">
          <FlightsTable flightsData={msg.flightsData} />
        </div>
      )}

      {msg.itineraryData && (
        <div className="mt-2">
          <ItineraryTable itineraryData={msg.itineraryData} />
        </div>
      )}
    </div>
  );
}