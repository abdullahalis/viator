import React from 'react';

type Flight = {
  departure_airport: { name: string; id: string; time: string };
  arrival_airport: { name: string; id: string; time: string };
  duration: number;
  airplane: string;
  airline: string;
  airline_logo: string;
  travel_class: string;
  flight_number: string;
  legroom: string;
  extensions: string[];
};

type FlightOption = {
  flights: Flight[];
  total_duration: number;
  carbon_emissions: {
    this_flight: number;
    typical_for_this_route: number;
    difference_percent: number;
  };
  price: number;
  type: string;
  airline_logo: string;
  extensions: string[];
};

type Props = {
  flightsData: FlightOption[];
};

export default function FlightsTable({ flightsData }: Props) {
  return (
    <div className="overflow-x-auto p-4">
      <table className="min-w-full border border-gray-200">
        <thead className="bg-gray-600">
          <tr>
            <th className="p-2 text-left">Airline</th>
            <th className="p-2 text-left">From → To</th>
            <th className="p-2 text-left">Departure / Arrival</th>
            <th className="p-2 text-left">Duration</th>
            <th className="p-2 text-left">Flight #</th>
            <th className="p-2 text-left">Price</th>
          </tr>
        </thead>
        <tbody>
          {flightsData.map((option, i) => {
            const firstFlight = option.flights[0]; // handle 1st leg as representative
            return (
              <tr key={i} className="border-t">
                <td className="p-2 whitespace-nowrap">
                <div className="flex items-center gap-2 min-w-0">
                    <img
                    src={firstFlight.airline_logo}
                    alt={firstFlight.airline}
                    className="w-8 h-8 object-contain"
                    />
                    <span className="truncate">{firstFlight.airline}</span>
                </div>
                </td>

                <td className="p-2">
                  {firstFlight.departure_airport.id} → {firstFlight.arrival_airport.id}
                </td>
                <td className="p-2">
                  {firstFlight.departure_airport.time} <br /> {firstFlight.arrival_airport.time}
                </td>
                <td className="p-2">
                  {Math.floor(option.total_duration / 60)}h {option.total_duration % 60}m
                </td>
                <td className="p-2">{firstFlight.flight_number}</td>
                <td className="p-2 font-semibold">${option.price}</td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
