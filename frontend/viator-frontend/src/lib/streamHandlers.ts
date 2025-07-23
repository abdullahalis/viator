export async function handleStreamedResponse({
  res,
  updateAssistantStream,
  finalizeAssistantMessage,
  setError,
}: {
  res: Response;
  updateAssistantStream: (msg: string) => void;
  finalizeAssistantMessage: (msg: string, toolsUsed?: string[], flightsData?: any, itineraryData?: any) => void;
  setError: (err: string | null) => void;
}) {
  const reader = res.body?.getReader();
  if (!reader) return;

  const decoder = new TextDecoder("utf-8");
  let done = false;
  let assistantMessage = "";
  let toolsUsed: string[] = [];
  let flightData: any = null;
  let itineraryData: any = null;

  try {
    while (!done) {
      const { value, done: streamDone } = await reader.read();
      done = streamDone;
      const text = decoder.decode(value);
    
      const chunks = text.trim().split("[END]"); // split with delimiter
      chunks.pop();

      for (const chunk of chunks) {
        const jsonChunk = JSON.parse(chunk);
        if (jsonChunk?.type === "tool") {
          toolsUsed.push(jsonChunk.tool_name);
        } else if (jsonChunk?.type === "flight_response") {
          assistantMessage += `\n${jsonChunk.message}\n`;
          flightData = jsonChunk.flights_data;
        } else if (jsonChunk?.type === "stream") {
          assistantMessage += jsonChunk.content;
          updateAssistantStream(assistantMessage);
        } else if (jsonChunk?.type === "itinerary_response") {
          itineraryData = jsonChunk.itinerary_data;
        } else if (jsonChunk?.type === "error") {
          setError("Error from tool: " + jsonChunk.tool);
        }
      }
    }

    finalizeAssistantMessage(assistantMessage, toolsUsed, flightData, itineraryData);
  } catch (err: any) {
    if (err.name === "AbortError") {
      setError("Stream aborted.");
    } else {
      setError(err.message || "An unexpected error occurred.");
    }
  }
}
