// src/components/HelpRequestList.tsx
"use client";

import { useState, useEffect } from "react";
import { db } from "@/lib/firebase";
import { collection, onSnapshot, query, where } from "firebase/firestore";
import RequestItem from "./RequestItem"; 

interface HelpRequest {
  id: string;
  question_text: string;
  status: string;
  supervisor_response?: string;
}

export default function HelpRequestList() {
  const [pendingRequests, setPendingRequests] = useState<HelpRequest[]>([]);
  const [resolvedRequests, setResolvedRequests] = useState<HelpRequest[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const pendingQuery = query(
      collection(db, "help_requests"),
      where("status", "==", "pending")
    );
    const unsubscribePending = onSnapshot(pendingQuery, (querySnapshot) => {
      const requestsData: HelpRequest[] = [];
      querySnapshot.forEach((doc) => {
        requestsData.push({ id: doc.id, ...doc.data() } as HelpRequest);
      });
      setPendingRequests(requestsData);
      setLoading(false);
    });

    const resolvedQuery = query(
      collection(db, "help_requests"),
      where("status", "==", "Resolved")
    );
    const unsubscribeResolved = onSnapshot(resolvedQuery, (querySnapshot) => {
      const requestsData: HelpRequest[] = [];
      querySnapshot.forEach((doc) => {
        requestsData.push({ id: doc.id, ...doc.data() } as HelpRequest);
      });
      setResolvedRequests(requestsData);
    });

    return () => {
      unsubscribePending();
      unsubscribeResolved();
    };
  }, []);

  if (loading) {
    return <p>Loading requests...</p>;
  }

  return (
    <div className="flex w-full max-w-6xl space-x-8">
      {/* --- LEFT COLUMN: Resolved Requests --- */}
      <div className="w-1/2">
        <h1 className="text-2xl font-bold mb-4">Resolved Requests ✅</h1>
        {resolvedRequests.length === 0 ? (
          <div className="p-4 border rounded-lg shadow-sm bg-gray-800 text-center">
            <p>No resolved requests yet.</p>
          </div>
        ) : (
          <ul className="space-y-4">
            {resolvedRequests.map((request) => (
              <RequestItem key={request.id} request={request} />
            ))}
          </ul>
        )}
      </div>

      {/* --- RIGHT COLUMN: Pending Requests --- */}
      <div className="w-1/2">
        <h1 className="text-2xl font-bold mb-4">Pending Help Requests ⏳</h1>
        {pendingRequests.length === 0 ? (
          <div className="p-4 border rounded-lg shadow-sm bg-gray-800 text-center">
            <p>🎉 No pending requests found. Great job!</p>
          </div>
        ) : (
          <ul className="space-y-4">
            {pendingRequests.map((request) => (
              <RequestItem key={request.id} request={request} />
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
