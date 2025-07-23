"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { ChevronDown, ChevronUp } from "lucide-react";

type Activity = {
  time: string;
  title: string;
  description: string;
};

type DayPlan = {
  date: string;
  activities: Activity[];
};

type ItineraryData = {
  location: string;
  days: DayPlan[];
};

export default function ItineraryTable({ itineraryData }: { itineraryData: ItineraryData }) {
    if (!itineraryData) {
        return <p>No itinerary data available.</p>;
    }
    // Parse string into JSON 
    itineraryData = typeof itineraryData === "string" ? JSON.parse(itineraryData) : itineraryData;

    // Keep track of Cards that have been expanded
    const [expandedDays, setExpandedDays] = useState<Record<string, boolean>>({});

    const toggleDay = (date: string) => {
        setExpandedDays((prev) => ({
        ...prev,
        [date]: !prev[date],
        }));
    };

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-semibold text-center">Itinerary for {itineraryData.location}</h2>
      {/* Map each day to its own card with activities and times */}
      {itineraryData.days.map((day) => (
        <Card key={day.date} className="p-4 rounded-2xl shadow-md">
          <div
            className="flex justify-between items-center cursor-pointer"
            onClick={() => toggleDay(day.date)}
          >
            <h3 className="text-xl font-medium">{new Date(day.date).toDateString()}</h3>
            {expandedDays[day.date] ? <ChevronUp /> : <ChevronDown />}
          </div>
          {/* Show full info if expanded */}
          {expandedDays[day.date] && (
            <div className="mt-4 space-y-4">
              {day.activities.map((activity, idx) => (
                <div
                  key={idx}
                  className="bg-gray-100 p-3 rounded-xl hover:bg-gray-200 transition"
                >
                  <div className="text-sm text-gray-500">{activity.time}</div>
                  <div className="font-semibold text-lg">{activity.title}</div>
                  <div className="text-sm text-gray-700">{activity.description}</div>
                </div>
              ))}
            </div>
          )}
        </Card>
      ))}
    </div>
  );
}
