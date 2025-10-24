// src/app/page.tsx
import HelpRequestList from "@/components/HelpRequestList";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <h1 className="text-3xl font-bold mb-6 text-center">
        Supervisor Dashboard
      </h1>
      <HelpRequestList />
    </main>
  );
}
