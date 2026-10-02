'use client';

import React, { useEffect, useState } from 'react';
import { getStoredUser, User } from '@/lib/api';
import {
  Activity,
  Mic,
  Calendar,
  Clock,
  ListTodo,
  TrendingUp,
  FileText,
  UploadCloud,
  Play
} from 'lucide-react';
import { Button } from '@/components/ui/button';

export default function DashboardPage() {
  const [user, setUser] = useState<User | null>(null);

  // Access is enforced by RequireAuth in app/dashboard/layout.tsx
  useEffect(() => {
    setUser(getStoredUser());
  }, []);

  if (!user) return null;

  return (
    <div className="min-h-screen pt-12 pb-24">
      <div className="container">
        
        {/* Header Section */}
        <div className="flex flex-col md:flex-row md:items-end justify-between gap-6 mb-12">
          <div>
            <h1 className="text-3xl font-bold tracking-tight mb-2">
              Welcome back, <span className="gradient-text">{user.first_name || 'User'}</span>
            </h1>
            <p className="text-slate-400">
              Here is what's happening with your meeting intelligence today.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <Button variant="secondary" className="!px-4">
              <Calendar size={18} className="text-slate-400" />
              <span>Schedule</span>
            </Button>
            <Button className="wave-ring !px-5 shadow-indigo-500/25">
              <UploadCloud size={18} />
              <span>Upload Audio</span>
            </Button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Mic size={120} className="text-indigo-400 -mr-8 -mt-8" />
            </div>
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-xl">
                <FileText size={22} />
              </div>
              <h3 className="font-semibold text-slate-300">Total Meetings</h3>
            </div>
            <p className="text-4xl font-bold tracking-tight">14</p>
            <div className="mt-3 flex items-center gap-1.5 text-emerald-400 text-sm font-medium">
              <TrendingUp size={16} />
              <span>+3 this week</span>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <Clock size={120} className="text-cyan-400 -mr-8 -mt-8" />
            </div>
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-cyan-500/20 text-cyan-400 rounded-xl">
                <Activity size={22} />
              </div>
              <h3 className="font-semibold text-slate-300">Hours Transcribed</h3>
            </div>
            <p className="text-4xl font-bold tracking-tight">8.5<span className="text-xl text-slate-500 ml-1">hrs</span></p>
            <div className="mt-3 flex items-center gap-1.5 text-slate-400 text-sm font-medium">
              <span>across all engines</span>
            </div>
          </div>

          <div className="glass-panel p-6 rounded-2xl relative overflow-hidden group">
            <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
              <ListTodo size={120} className="text-rose-400 -mr-8 -mt-8" />
            </div>
            <div className="flex items-center gap-4 mb-4">
              <div className="p-3 bg-rose-500/20 text-rose-400 rounded-xl">
                <ListTodo size={22} />
              </div>
              <h3 className="font-semibold text-slate-300">Pending Actions</h3>
            </div>
            <p className="text-4xl font-bold tracking-tight">6</p>
            <div className="mt-3 flex items-center gap-1.5 text-rose-400 text-sm font-medium">
              <span>2 high priority</span>
            </div>
          </div>
        </div>

        {/* Recent Meetings List */}
        <div>
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-bold tracking-tight">Recent Transcripts</h2>
            <Button variant="ghost">View All</Button>
          </div>
          
          <div className="glass-panel rounded-2xl overflow-hidden divide-y divide-white/5 border-white/10">
            {/* Demo Item 1 */}
            <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-indigo-500/20 text-indigo-400 rounded-xl shrink-0 mt-1">
                  <Play size={20} className="ml-0.5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg mb-1">Q3 Strategic Product Roadmap & Security</h4>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Calendar size={14} /> Oct 02, 2026
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock size={14} /> 45 mins
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 md:flex-col md:items-end">
                <span className="badge badge-confidential">Confidential</span>
                <span className="text-xs text-slate-500 font-mono">Faster-Whisper (CPU)</span>
              </div>
            </div>

            {/* Demo Item 2 */}
            <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-cyan-500/20 text-cyan-400 rounded-xl shrink-0 mt-1">
                  <Play size={20} className="ml-0.5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg mb-1">Weekly Cross-Functional Growth Sync</h4>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Calendar size={14} /> Sep 28, 2026
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock size={14} /> 28 mins
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 md:flex-col md:items-end">
                <span className="badge badge-public">Public</span>
                <span className="text-xs text-slate-500 font-mono">Cloud Deepgram API</span>
              </div>
            </div>
            
            {/* Demo Item 3 */}
            <div className="p-5 flex flex-col md:flex-row md:items-center justify-between gap-4 hover:bg-white/[0.02] transition-colors">
              <div className="flex items-start gap-4">
                <div className="p-3 bg-emerald-500/20 text-emerald-400 rounded-xl shrink-0 mt-1">
                  <Play size={20} className="ml-0.5" />
                </div>
                <div>
                  <h4 className="font-bold text-lg mb-1">Engineering Architecture Standup</h4>
                  <div className="flex flex-wrap items-center gap-3 text-sm text-slate-400">
                    <span className="flex items-center gap-1.5">
                      <Calendar size={14} /> Sep 25, 2026
                    </span>
                    <span className="flex items-center gap-1.5">
                      <Clock size={14} /> 15 mins
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-3 md:flex-col md:items-end">
                <span className="badge badge-confidential">Confidential</span>
                <span className="text-xs text-slate-500 font-mono">Faster-Whisper (CPU)</span>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
