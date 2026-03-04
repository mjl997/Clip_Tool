"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Link2, Loader2 } from "lucide-react";

export default function Home() {
  const [url, setUrl] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url) return;

    setIsLoading(true);
    try {
      const response = await fetch("/api/v1/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url }),
      });

      if (!response.ok) throw new Error("Failed to submit video");

      const data = await response.json();
      toast.success("Video submitted successfully!");
      router.push(`/processing/${data.job_id}`);
    } catch (error) {
      toast.error("Error submitting video");
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 bg-background">
      <div className="w-full max-w-xl space-y-8 text-center">
        <h1 className="text-4xl font-bold tracking-tight lg:text-5xl bg-gradient-to-r from-blue-500 to-purple-500 bg-clip-text text-transparent">
          Clip Tool
        </h1>
        <p className="text-muted-foreground text-lg">
          Transform long videos into viral clips automatically with AI.
        </p>

        <form onSubmit={handleSubmit} className="flex gap-2">
          <div className="relative flex-1">
            <Link2 className="absolute left-3 top-3 h-5 w-5 text-muted-foreground" />
            <Input
              type="url"
              placeholder="Paste YouTube URL here..."
              className="pl-10 h-12 text-lg"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              required
            />
          </div>
          <Button type="submit" size="lg" className="h-12 px-8" disabled={isLoading}>
            {isLoading ? <Loader2 className="mr-2 h-4 w-4 animate-spin" /> : "Process"}
          </Button>
        </form>

        <div className="text-sm text-muted-foreground">
          Supported: YouTube, MP4 URLs
        </div>
      </div>
    </div>
  );
}
