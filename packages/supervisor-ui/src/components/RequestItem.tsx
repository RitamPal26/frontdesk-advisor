// src/components/RequestItem.tsx
"use client";

import { useState } from "react";
import { db } from "@/lib/firebase";
import {
  doc,
  updateDoc,
  addDoc,
  collection,
  serverTimestamp,
} from "firebase/firestore";

interface HelpRequest {
  id: string;
  question_text: string;
  status: string;
  supervisor_response?: string;
}

interface RequestItemProps {
  request: HelpRequest;
}

const generateKeywords = (question: string): string[] => {
  const stopWords = new Set([
    "is",
    "a",
    "the",
    "what",
    "how",
    "for",
    "of",
    "a",
  ]);
  return question
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, "") // Remove punctuation
    .split(/\s+/)
    .filter((word) => word && !stopWords.has(word));
};

export default function RequestItem({ request }: RequestItemProps) {
  const [answer, setAnswer] = useState("");
  const [category, setCategory] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!answer.trim() || !category.trim()) {
      alert("Please provide both an answer and a category.");
      return;
    }

    try {
      const requestRef = doc(db, "help_requests", request.id);
      await updateDoc(requestRef, {
        status: "Resolved",
        supervisor_response: answer,
        resolved_at: serverTimestamp(),
      });

      await addDoc(collection(db, "knowledge_base"), {
        question_text: request.question_text,
        answer_text: answer,
        category: category,
        question_keywords: generateKeywords(request.question_text),
        created_at: serverTimestamp(),
        flagged_for_review: false,
        schema_version: 2,
        usage_count: 0,
      });

      setAnswer("");
      setCategory("");
    } catch (error) {
      console.error("Error processing request: ", error);
      alert("Failed to resolve request.");
    }
  };

  if (request.status === "Resolved") {
    return (
      <li className="p-4 border rounded-lg shadow-sm bg-gray-800 text-white">
        <div className="mb-2">
          <p className="font-semibold text-gray-400">Question:</p>
          <p>{request.question_text}</p>
        </div>
        <div>
          <p className="font-semibold text-gray-400">Answer:</p>
          <p className="text-green-400">{request.supervisor_response}</p>
        </div>
      </li>
    );
  }

  return (
    <li className="p-4 border rounded-lg shadow-sm bg-gray-800">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block mb-2 font-medium">Question:</label>
          <p className="p-3 rounded-md bg-gray-700">{request.question_text}</p>
        </div>
        <div>
          <textarea
            value={answer}
            onChange={(e) => setAnswer(e.target.value)}
            placeholder="Type your answer here..."
            className="w-full p-2 border rounded-md bg-gray-700 border-gray-600 focus:ring-blue-500 focus:border-blue-500"
            rows={3}
            required
          />
        </div>
        <div>
          <input
            type="text"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            placeholder="Enter a category (e.g., Pricing, Services)"
            className="w-full p-2 border rounded-md bg-gray-700 border-gray-600 focus:ring-blue-500 focus:border-blue-500"
            required
          />
        </div>
        <button
          type="submit"
          className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
        >
          Submit Answer & Add to Knowledge Base
        </button>
      </form>
    </li>
  );
}
