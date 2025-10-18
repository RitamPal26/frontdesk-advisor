// src/components/RequestItem.tsx
"use client";

import { useState } from "react";
import { db } from "@/lib/firebase";
import { doc, updateDoc } from "firebase/firestore";

// Reuse the interface, or define it again if needed
interface HelpRequest {
  id: string;
  question_text: string;
  status: string;
}

export default function RequestItem({ request }: { request: HelpRequest }) {
  const [responseText, setResponseText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleResolve = async () => {
    if (!responseText.trim()) {
      alert("Please enter a response.");
      return;
    }
    setIsSubmitting(true);

    // Get a reference to the specific document in Firestore
    const requestDocRef = doc(db, "help_requests", request.id);

    try {
      // Update the document with the new status and response
      await updateDoc(requestDocRef, {
        status: "Resolved",
        supervisor_response: responseText,
        resolved_at: new Date(), // Add a resolved timestamp
      });
      // The item will disappear from the list automatically thanks to the real-time listener!
    } catch (error) {
      console.error("Error resolving request:", error);
      alert("Failed to resolve request. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <li className="p-4 border rounded-lg shadow-sm bg-gray-800 space-y-3">
      <div>
        <p className="font-semibold text-gray-300">Question:</p>
        <p className="text-gray-400">{request.question_text}</p>
      </div>
      <div>
        <textarea
          value={responseText}
          onChange={(e) => setResponseText(e.target.value)}
          placeholder="Type your answer here..."
          className="w-full p-2 border rounded bg-gray-700 text-white border-gray-600 focus:ring-blue-500 focus:border-blue-500"
          rows={2}
        />
      </div>
      <button
        onClick={handleResolve}
        disabled={isSubmitting}
        className="w-full px-4 py-2 font-bold text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:bg-gray-500"
      >
        {isSubmitting ? "Submitting..." : "Submit Answer & Resolve"}
      </button>
    </li>
  );
}
