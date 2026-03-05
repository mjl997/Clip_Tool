"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Progress } from "@/components/ui/progress";
import { Loader2 } from "lucide-react";

export default function ProcessingPage({ params }: { params: { jobId: string } }) {
  const [status, setStatus] = useState("initializing");
  const [progress, setProgress] = useState(0);
  const router = useRouter();
  const { jobId } = params;

  useEffect(() => {
    const pollStatus = async () => {
      try {
        // Check multiple services for status
        // Pipeline: Ingest -> Transcribe -> Analyze -> ClipGen
        
        // 1. Check Ingest
        const ingestRes = await fetch(`/api/v1/ingest/${jobId}`);
        const ingestData = await ingestRes.json();
        
        if (ingestData.status === "pending" || ingestData.status === "downloading") {
          setStatus("Downloading video...");
          setProgress(25);
          return;
        }
        
        // 2. Check Transcription
        const transRes = await fetch(`/api/v1/transcription/${jobId}`);
        const transData = await transRes.json();
        
        if (transData.status === "transcribing") {
          setStatus("Transcribing audio...");
          setProgress(50);
          return;
        }
        
        // 3. Check Analysis
        const analysisRes = await fetch(`/api/v1/analysis/${jobId}`);
        const analysisData = await analysisRes.json();
        
        if (analysisData.status === "analyzing") {
          setStatus("Analyzing viral potential...");
          setProgress(75);
          return;
        }
        
        // 4. Check ClipGen
        const clipsRes = await fetch(`/api/v1/clips/${jobId}`);
        const clipsData = await clipsRes.json();
        
        if (clipsData.status === "completed" || clipsData.status === "clips_ready") {
          setStatus("Completed!");
          setProgress(100);
          router.push(`/results/${jobId}`);
          return;
        }
        
        if (clipsData.status === "clipping") {
           setStatus("Generating clips...");
           setProgress(90);
           return;
        }
        
        // If failed
        if ([ingestData.status, transData.status, analysisData.status, clipsData.status].includes("failed")) {
            setStatus("Error processing video");
            return;
        }

      } catch (error) {
        console.error("Polling error", error);
      }
    };

    const interval = setInterval(pollStatus, 2000);
    return () => clearInterval(interval);
  }, [jobId, router]);

  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-8 bg-background">
      <div className="w-full max-w-md space-y-6 text-center">
        <Loader2 className="w-12 h-12 mx-auto animate-spin text-primary" />
        <h2 className="text-2xl font-bold">{status}</h2>
        <Progress value={progress} className="w-full h-2" />
        <p className="text-muted-foreground">
          This usually takes a few minutes depending on video length.
        </p>
      </div>
    </div>
  );
}
