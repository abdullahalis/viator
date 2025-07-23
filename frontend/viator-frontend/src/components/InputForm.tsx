// components/InputForm.tsx
"use client";

import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import React from "react";

type InputFormProps = {
  input: string;
  setInput: (val: string) => void;
  isLoading: boolean;
  handleSubmit: (e: React.FormEvent) => void;
  handleStop: () => void;
};

export default function InputForm({
  input,
  setInput,
  isLoading,
  handleSubmit,
  handleStop,
}: InputFormProps) {
  return (
    <form
      onSubmit={handleSubmit}
      className="absolute bottom-8 left-1/2 -translate-x-1/2 w-[85%] border-t border-gray-300 bg-white p-4 flex gap-2 shadow-md rounded-xl"
      style={{ maxWidth: "900px" }}
    >
      <Input
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Ask about your next trip..."
        className="flex-1 border border-gray-300 bg-white text-gray-800 rounded-lg"
      />
      {isLoading ? (
        <Button
          type="button"
          onClick={handleStop}
          className="bg-red-500 hover:bg-red-600 text-white rounded-lg cursor-pointer"
        >
          Stop
        </Button>
      ) : (
        <Button
          type="submit"
          className="bg-secondary text-white hover:bg-accent rounded-lg cursor-pointer"
        >
          Send
        </Button>
      )}
    </form>
  );
}
