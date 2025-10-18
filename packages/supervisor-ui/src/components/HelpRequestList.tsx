// src/components/HelpRequestList.tsx
"use client";

import { useState, useEffect } from "react";
import { db } from "@/lib/firebase";
import { collection, onSnapshot, query, where } from "firebase/firestore";
import RequestItem from "./RequestItem"; // Import the new component

interface HelpRequest {
  id: string;
  question_text: string;
  status: string;
}

export default function HelpRequestList() {
  const [requests, setRequests] = useState<HelpRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const q = query(
      collection(db, "help_requests"),
      where("status", "==", "Pending")
    );

    const unsubscribe = onSnapshot(q, (querySnapshot) => {
      const requestsData: HelpRequest[] = [];
      querySnapshot.forEach((doc) => {
        requestsData.push({ id: doc.id, ...doc.data() } as HelpRequest);
      });
      setRequests(requestsData);
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  if (loading) {
    return <p>Loading pending requests...</p>;
  }

  return (
    <div>
      <h1 className="text-2xl font-bold mb-4">Pending Help Requests</h1>
      {requests.length === 0 ? (
        <div className="p-4 border rounded-lg shadow-sm bg-gray-800 text-center">
          <p>🎉 No pending requests found. Great job!</p>
        </div>
      ) : (
        <ul className="space-y-4">
          {requests.map((request) => (
            <RequestItem key={request.id} request={request} />
          ))}
        </ul>
      )}
    </div>
  );
}
