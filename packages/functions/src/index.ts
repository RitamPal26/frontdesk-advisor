// packages/functions/src/index.ts
import {onDocumentUpdated} from "firebase-functions/v2/firestore";
import * as logger from "firebase-functions/logger";
import * as admin from "firebase-admin";

admin.initializeApp();
const db = admin.firestore();

// This is the new V2 syntax for a Firestore trigger
export const onHelpRequestResolved = onDocumentUpdated(
  "help_requests/{requestId}",
  async (event) => {
    // The event object contains all the information
    const beforeData = event.data?.before.data();
    const afterData = event.data?.after.data();

    // Check if the status changed from 'Pending' to 'Resolved'
    if (beforeData?.status === "Pending" && afterData?.status === "Resolved") {
      const requestId = event.params.requestId;
      logger.log(`Help request ${requestId} was resolved.`);

      const customerId = afterData.customer_id;
      const question_text = afterData.question_text;
      const answer_text = afterData.supervisor_response;

      // 1. Simulate texting back the original caller
      logger.log(
        `Simulating text back to ${customerId}: "Regarding your question '${question_text}', the answer is: ${answer_text}"`
      );

      // 2. Update the internal knowledge base
      try {
        await db.collection("knowledge_base").add({
          question_text: question_text,
          answer_text: answer_text,
          learned_at: new Date(),
        });
        logger.log("Successfully updated the knowledge base.");
      } catch (error) {
        logger.error("Error updating knowledge base:", error);
      }
    }
    return null;
  }
);
