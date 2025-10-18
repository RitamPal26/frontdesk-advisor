// src/app/page.tsx
import HelpRequestList from "@/components/HelpRequestList";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center p-24">
      <div className="w-full max-w-4xl">
        <HelpRequestList />
      </div>
    </main>
  );
}
