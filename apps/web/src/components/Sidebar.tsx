"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Home, Settings, Clock, Activity, Menu, X } from "lucide-react";

export function Sidebar() {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(false);
  const [recentJobs, setRecentJobs] = useState<any[]>([]);

  useEffect(() => {
    // Fetch recent jobs
    const fetchJobs = async () => {
      try {
        const res = await fetch("/api/v1/jobs?limit=5");
        if (res.ok) {
          const data = await res.json();
          if (Array.isArray(data)) {
            setRecentJobs(data);
          } else {
            setRecentJobs([]);
          }
        }
      } catch (e) {
        console.error("Failed to fetch jobs");
      }
    };
    fetchJobs();
    // Poll for updates every 10s
    const interval = setInterval(fetchJobs, 10000);
    return () => clearInterval(interval);
  }, []);

  const toggle = () => setIsOpen(!isOpen);

  return (
    <>
      <Button 
        variant="ghost" 
        size="icon" 
        className="fixed top-4 left-4 z-50 md:hidden"
        onClick={toggle}
      >
        {isOpen ? <X /> : <Menu />}
      </Button>

      <div className={cn(
        "fixed inset-y-0 left-0 z-40 w-64 bg-card border-r transition-transform transform md:translate-x-0",
        isOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        <div className="flex flex-col h-full p-4">
          <div className="flex items-center gap-2 mb-8 px-2">
            <Activity className="h-6 w-6 text-primary" />
            <span className="text-xl font-bold">Clip Tool</span>
          </div>

          <nav className="space-y-2 mb-8">
            <Link href="/">
              <Button variant={pathname === "/" ? "secondary" : "ghost"} className="w-full justify-start">
                <Home className="mr-2 h-4 w-4" />
                Input
              </Button>
            </Link>
            <Link href="/settings">
              <Button variant={pathname === "/settings" ? "secondary" : "ghost"} className="w-full justify-start">
                <Settings className="mr-2 h-4 w-4" />
                Settings
              </Button>
            </Link>
          </nav>

          <div className="flex-1 overflow-y-auto">
            <h3 className="text-sm font-semibold text-muted-foreground mb-4 px-2 flex items-center">
              <Clock className="mr-2 h-4 w-4" /> Recent Jobs
            </h3>
            <div className="space-y-1">
              {recentJobs.map((job) => (
                <Link key={job.id} href={job.status === "completed" ? `/results/${job.id}` : `/processing/${job.id}`}>
                  <Button variant="ghost" className="w-full justify-start text-xs truncate h-auto py-2 block text-left">
                    <div className="truncate font-medium">{job.metadata?.title || job.id}</div>
                    <div className={cn("text-[10px]", 
                      job.status === "completed" ? "text-green-500" : 
                      job.status === "failed" ? "text-red-500" : "text-yellow-500"
                    )}>
                      {job.status}
                    </div>
                  </Button>
                </Link>
              ))}
              {recentJobs.length === 0 && (
                <div className="px-2 text-xs text-muted-foreground">No recent jobs</div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
