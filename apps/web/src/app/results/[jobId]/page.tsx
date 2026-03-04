"use client";

import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Download, Play, Share2 } from "lucide-react";
import Link from "next/link";

interface Clip {
  clip_id: string;
  start: number;
  end: number;
  score: number;
  clean_video: string;
  subbed_video: string;
  thumbnail: string;
  category: string;
  hook: string;
}

export default function ResultsPage({ params }: { params: { jobId: string } }) {
  const [clips, setClips] = useState<Clip[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const { jobId } = params;

  useEffect(() => {
    const fetchClips = async () => {
      try {
        const response = await fetch(`/api/v1/clips/${jobId}`);
        const data = await response.json();
        
        if (data.status === "completed" || data.status === "clips_ready") {
          setClips(data.clips);
        } else {
          toast.error("Clips not ready yet");
        }
      } catch (error) {
        toast.error("Failed to load clips");
      } finally {
        setIsLoading(false);
      }
    };
    fetchClips();
  }, [jobId]);

  const handleDownload = (clipId: string, format: string) => {
    // Trigger download
    const url = `/api/v1/export/${jobId}/${clipId}?format=${format}`;
    window.open(url, "_blank");
  };

  const handleDownloadAll = () => {
    // const url = `/api/v1/export/${jobId}/all`;
    // window.open(url, "_blank");
    
    // Download clips individually for now since bulk zip is unstable
    clips.forEach(clip => {
      const url = `/api/v1/export/${jobId}/${clip.clip_id}?format=mp4_subs`;
      // Use a small delay to avoid browser blocking multiple popups
      setTimeout(() => window.open(url, "_blank"), 500);
    });
  };

  if (isLoading) return <div className="p-8 text-center">Loading results...</div>;

  return (
    <div className="container mx-auto p-6 space-y-8">
      <header className="flex justify-between items-center">
        <h1 className="text-3xl font-bold">Viral Clips Generated</h1>
        <Button onClick={handleDownloadAll} variant="secondary">
          <Download className="mr-2 h-4 w-4" /> Download All (ZIP)
        </Button>
      </header>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {clips.map((clip) => (
          <Card key={clip.clip_id} className="overflow-hidden">
            <div className="relative aspect-[9/16] bg-black">
              {/* Simple video player or thumbnail */}
              <video 
                src={`/api/v1/export/${jobId}/${clip.clip_id}?format=mp4_subs`} 
                controls 
                poster={`/api/v1/export/${jobId}/${clip.clip_id}/thumb.jpg`} // Assuming we expose thumb endpoint or use presigned
                className="w-full h-full object-cover"
              />
              <div className="absolute top-2 right-2 bg-green-500 text-white px-2 py-1 rounded-full text-xs font-bold">
                Score: {clip.score}
              </div>
            </div>
            
            <CardHeader>
              <CardTitle className="text-lg line-clamp-2">{clip.hook || "No hook detected"}</CardTitle>
            </CardHeader>
            
            <CardContent>
              <div className="flex justify-between text-sm text-muted-foreground">
                <span>{clip.category || "General"}</span>
                <span>{Math.round(clip.end - clip.start)}s</span>
              </div>
            </CardContent>
            
            <CardFooter className="flex gap-2">
              <Button 
                variant="outline" 
                size="sm" 
                className="flex-1"
                onClick={() => handleDownload(clip.clip_id, "mp4_subs")}
              >
                <Download className="mr-2 h-4 w-4" /> MP4
              </Button>
              <Button 
                variant="ghost" 
                size="icon"
                onClick={() => {
                  if (clip.hook) {
                    navigator.clipboard.writeText(clip.hook);
                    toast.success("Caption copied!");
                  }
                }}
              >
                <Share2 className="h-4 w-4" />
              </Button>
            </CardFooter>
          </Card>
        ))}
      </div>
      
      {clips.length === 0 && (
        <div className="text-center py-12 text-muted-foreground">
          No clips generated. Try adjusting settings or use a different video.
        </div>
      )}
    </div>
  );
}
