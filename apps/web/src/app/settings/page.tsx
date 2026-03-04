"use client";

import { useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function SettingsPage() {
  const [keys, setKeys] = useState({
    openai: "",
    anthropic: "",
  });

  const handleSave = () => {
    // Save to localStorage or API
    // For now, we assume these are set in env, but user might want to override?
    // In this architecture, API keys are in backend env. 
    // Frontend settings might just be preferences like "Model" or "Language".
    
    // If we want to allow user to provide keys, we need an endpoint to update backend env or pass them in every request.
    // Passing in every request is safer for multi-user, but this is a local tool.
    // Let's assume we just save preferences.
    
    localStorage.setItem("clip-tool-settings", JSON.stringify(keys));
    toast.success("Settings saved");
  };

  return (
    <div className="container mx-auto p-8 max-w-2xl">
      <h1 className="text-3xl font-bold mb-8">Settings</h1>
      
      <Card className="mb-6">
        <CardHeader>
          <CardTitle>API Keys (Optional Override)</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <label className="text-sm font-medium">OpenAI API Key</label>
            <Input 
              type="password" 
              placeholder="sk-..." 
              value={keys.openai}
              onChange={(e) => setKeys({...keys, openai: e.target.value})}
            />
          </div>
          <div className="space-y-2">
            <label className="text-sm font-medium">Anthropic API Key</label>
            <Input 
              type="password" 
              placeholder="sk-ant-..." 
              value={keys.anthropic}
              onChange={(e) => setKeys({...keys, anthropic: e.target.value})}
            />
          </div>
        </CardContent>
      </Card>

      <Card className="mb-6">
        <CardHeader>
          <CardTitle>Preferences</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
           <div className="space-y-2">
            <label className="text-sm font-medium">Default Model</label>
            <select className="w-full p-2 border rounded bg-background">
              <option>GPT-4 Turbo</option>
              <option>Claude 3 Opus</option>
            </select>
          </div>
        </CardContent>
      </Card>

      <Button onClick={handleSave}>Save Changes</Button>
    </div>
  );
}
