/**
 * Settings Page — Upload CSV → Preview Meetings → Upload Transcripts → Analyze
 */

import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyze, parsePreview, getHealth } from '@/lib/api';
import { useSession } from '@/contexts/SessionContext';
import type { MeetingPreview } from '@/types/api';

function formatDate(dt: string): string {
  try {
    return new Date(dt).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  } catch {
    return dt;
  }
}

export function Settings() {
  const navigate = useNavigate();
  const { setSessionId } = useSession();

  const [step, setStep] = useState<'upload' | 'preview'>('upload');
  const [historicalCsv, setHistoricalCsv] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);

  const [meetings, setMeetings] = useState<MeetingPreview[]>([]);
  const [transcripts, setTranscripts] = useState<Record<number, File>>({});

  const [isPreviewing, setIsPreviewing] = useState(false);
  const [previewError, setPreviewError] = useState<string | null>(null);

  const [hourlyRate, setHourlyRate] = useState(75);
  const [costWeight, setCostWeight] = useState(0.25);
  const [decisionWeight, setDecisionWeight] = useState(0.40);
  const [participationWeight, setParticipationWeight] = useState(0.20);
  const [recurrenceWeight, setRecurrenceWeight] = useState(0.15);

  const [ollamaConnected, setOllamaConnected] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getHealth().then((d) => setOllamaConnected(d.ollama_connected)).catch(() => {});
  }, []);

  const weightSum = costWeight + decisionWeight + participationWeight + recurrenceWeight;
  const weightsValid = Math.abs(weightSum - 1.0) < 0.01;

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files[0];
    if (file?.name.endsWith('.csv')) {
      setHistoricalCsv(file);
      setMeetings([]);
      setTranscripts({});
      setStep('upload');
    }
  };

  const handleCsvInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setHistoricalCsv(file);
      setMeetings([]);
      setTranscripts({});
      setStep('upload');
    }
    e.target.value = '';
  };

  const handlePreview = async () => {
    if (!historicalCsv) return;
    setIsPreviewing(true);
    setPreviewError(null);
    try {
      const result = await parsePreview(historicalCsv);
      setMeetings(result);
      setStep('preview');
    } catch (err) {
      setPreviewError(err instanceof Error ? err.message : 'Preview failed');
    } finally {
      setIsPreviewing(false);
    }
  };

  const handleTranscriptInput = (index: number, e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setTranscripts((prev) => ({ ...prev, [index]: file }));
    }
    e.target.value = '';
  };

  const removeTranscript = (index: number) => {
    setTranscripts((prev) => {
      const next = { ...prev };
      delete next[index];
      return next;
    });
  };

  const handleAnalyze = async () => {
    if (!historicalCsv) return;
    setIsAnalyzing(true);
    setError(null);
    try {
      const transcriptTexts: Record<number, string> = {};
      for (const [idx, file] of Object.entries(transcripts)) {
        transcriptTexts[Number(idx)] = await file.text();
      }
      const response = await analyze(
        historicalCsv,
        null,
        {
          hourly_rate: hourlyRate,
          cost_weight: costWeight,
          decision_deficit_weight: decisionWeight,
          participation_weight: participationWeight,
          recurrence_weight: recurrenceWeight,
        },
        transcriptTexts
      );
      setSessionId(response.session_id);
      navigate('/');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Analysis failed');
    } finally {
      setIsAnalyzing(false);
    }
  };

  // ── STEP 1: Upload CSV ─────────────────────────────────────────────────────
  if (step === 'upload') {
    return (
      <div className="max-w-3xl mx-auto">
        <h1 className="font-display font-black text-5xl uppercase mb-2 text-kb-black">
          UPLOAD DATA
        </h1>
        <p className="font-mono text-xs uppercase tracking-widest text-kb-black/50 mb-10">
          Upload your meeting calendar export to get started
        </p>

        {/* Drop zone */}
        <div
          className={`border-3 border-dashed ${isDragging ? 'border-kb-lavender bg-kb-lavender' : 'border-kb-black bg-kb-white'} p-16 text-center transition-colors duration-75 mb-6 shadow-brutal-md`}
          onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
          onDragLeave={() => setIsDragging(false)}
          onDrop={handleDrop}
        >
          <div className="text-6xl mb-4">📅</div>
          <p className="font-mono font-bold text-sm uppercase tracking-widest text-kb-black mb-2">
            DROP YOUR MEETINGS.CSV HERE
          </p>
          <p className="font-mono text-xs text-kb-black/50 mb-6">
            Export from Google Calendar, Outlook, or any standard calendar app
          </p>
          <input
            type="file"
            accept=".csv"
            onChange={handleCsvInput}
            className="hidden"
            id="csv-input"
          />
          <label
            htmlFor="csv-input"
            className="inline-block border-3 border-kb-black bg-kb-white px-8 py-4 font-mono font-bold text-sm uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none cursor-pointer transition-all duration-75"
          >
            BROWSE FILES
          </label>
        </div>

        {/* File selected */}
        {historicalCsv && (
          <div className="bg-kb-mint border-3 border-kb-black shadow-brutal-sm p-4 flex items-center justify-between mb-6">
            <div className="flex items-center gap-3">
              <span className="text-xl">✓</span>
              <div>
                <div className="font-mono font-bold text-sm text-kb-black">{historicalCsv.name}</div>
                <div className="font-mono text-xs text-kb-black/50">
                  {(historicalCsv.size / 1024).toFixed(1)} KB
                </div>
              </div>
            </div>
            <button
              onClick={() => { setHistoricalCsv(null); setMeetings([]); setTranscripts({}); }}
              className="font-mono font-bold text-sm text-kb-coral hover:opacity-70 transition-opacity"
            >
              REMOVE
            </button>
          </div>
        )}

        {previewError && (
          <div className="bg-kb-coral border-3 border-kb-black p-4 shadow-brutal-sm mb-6">
            <p className="font-sans font-bold text-sm text-kb-black">⚠ {previewError}</p>
          </div>
        )}

        <button
          onClick={handlePreview}
          disabled={!historicalCsv || isPreviewing}
          className="w-full border-3 border-kb-black bg-kb-pink shadow-brutal-md py-5 font-mono font-black text-xl uppercase tracking-widest hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0 disabled:hover:shadow-brutal-md"
        >
          {isPreviewing ? 'PARSING...' : 'PREVIEW MEETINGS →'}
        </button>

        <div className="mt-6 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full flex-shrink-0 ${ollamaConnected ? 'bg-kb-mint' : 'bg-kb-coral'}`} />
          <span className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
            OLLAMA: {ollamaConnected ? 'CONNECTED' : 'OFFLINE — LLM FEATURES DISABLED'}
          </span>
        </div>
      </div>
    );
  }

  // ── STEP 2: Preview + Transcripts + Config ─────────────────────────────────
  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="font-display font-black text-4xl uppercase mb-1">
            {meetings.length} MEETINGS FOUND
          </h1>
          <p className="font-mono text-xs uppercase tracking-widest text-kb-black/50">
            {historicalCsv?.name} · Optionally upload transcripts below
          </p>
        </div>
        <button
          onClick={() => { setStep('upload'); setMeetings([]); setTranscripts({}); }}
          className="border-2 border-kb-black bg-kb-white px-4 py-2 font-mono font-bold text-xs uppercase tracking-widest shadow-brutal-sm hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75"
        >
          ← CHANGE FILE
        </button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Meeting list */}
        <div className="lg:col-span-2">
          <div className="border-3 border-kb-black shadow-brutal-md overflow-hidden">
            {/* Table header */}
            <div className="bg-kb-black text-kb-white grid grid-cols-[auto_1fr_auto_auto_auto] gap-0">
              <div className="px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">#</div>
              <div className="px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10">MEETING</div>
              <div className="px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10 text-center">DUR</div>
              <div className="px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest border-r-2 border-white/10 text-center">PPL</div>
              <div className="px-4 py-3 font-mono font-bold text-xs uppercase tracking-widest text-center min-w-[120px]">TRANSCRIPT</div>
            </div>

            {/* Meeting rows */}
            {meetings.map((m) => {
              const hasTranscript = m.index in transcripts;
              return (
                <div
                  key={m.index}
                  className={`grid grid-cols-[auto_1fr_auto_auto_auto] gap-0 border-b-2 border-kb-black last:border-b-0 ${
                    hasTranscript ? 'bg-kb-mint/20' : 'bg-kb-white hover:bg-kb-muted'
                  } transition-colors duration-75`}
                >
                  {/* Index */}
                  <div className="px-4 py-3 border-r-2 border-kb-black flex items-center">
                    <span className="font-mono font-bold text-xs text-kb-black/40 w-5">{m.index + 1}</span>
                  </div>

                  {/* Title + date */}
                  <div className="px-4 py-3 border-r-2 border-kb-black flex flex-col justify-center min-w-0">
                    <div className="font-mono font-bold text-sm text-kb-black truncate">
                      {m.title}
                    </div>
                    <div className="font-mono text-xs text-kb-black/40 mt-0.5">
                      {formatDate(m.start_datetime)}
                      {m.is_recurring && (
                        <span className="ml-2 bg-kb-lavender border border-kb-black px-1 font-bold">
                          RECURRING
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Duration */}
                  <div className="px-4 py-3 border-r-2 border-kb-black flex items-center justify-center">
                    <span className="font-mono text-xs text-kb-black whitespace-nowrap">{m.duration_minutes}m</span>
                  </div>

                  {/* Attendees */}
                  <div className="px-4 py-3 border-r-2 border-kb-black flex items-center justify-center">
                    <span className="font-mono text-xs text-kb-black">{m.attendee_count}</span>
                  </div>

                  {/* Transcript upload */}
                  <div className="px-3 py-2 flex items-center justify-center min-w-[120px]">
                    {hasTranscript ? (
                      <div className="flex items-center gap-1">
                        <span className="font-mono text-xs text-kb-black truncate max-w-[72px]" title={transcripts[m.index].name}>
                          {transcripts[m.index].name.slice(0, 8)}…
                        </span>
                        <button
                          onClick={() => removeTranscript(m.index)}
                          className="font-mono font-bold text-xs text-kb-coral hover:opacity-70 flex-shrink-0"
                        >
                          ×
                        </button>
                      </div>
                    ) : (
                      <>
                        <input
                          type="file"
                          accept=".txt"
                          onChange={(e) => handleTranscriptInput(m.index, e)}
                          className="hidden"
                          id={`transcript-${m.index}`}
                        />
                        <label
                          htmlFor={`transcript-${m.index}`}
                          className="border-2 border-kb-black bg-kb-white px-2 py-1 font-mono font-bold text-xs uppercase tracking-widest shadow-brutal-sm hover:bg-kb-lavender hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-brutal-none cursor-pointer transition-all duration-75 whitespace-nowrap"
                        >
                          + TXT
                        </label>
                      </>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {Object.keys(transcripts).length > 0 && (
            <div className="mt-3 font-mono text-xs uppercase tracking-widest text-kb-black/50">
              {Object.keys(transcripts).length} transcript{Object.keys(transcripts).length !== 1 ? 's' : ''} uploaded — LLM will extract action items & decisions from these
            </div>
          )}
        </div>

        {/* Right: Config + Analyze */}
        <div className="space-y-6">
          <div className="bg-kb-white border-3 border-kb-black shadow-brutal-md p-6">
            <h2 className="font-display font-black text-xl uppercase mb-6 text-kb-black">
              ANALYSIS CONFIG
            </h2>

            <div className="space-y-5">
              {/* Hourly rate */}
              <div>
                <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black block mb-1">
                  HOURLY RATE ($/HR)
                </label>
                <p className="font-sans text-xs text-kb-black/50 mb-2">
                  Average fully-loaded hourly cost per employee (salary + benefits). Use $50–75 for junior roles, $100–150 for senior.
                </p>
                <input
                  type="number"
                  value={hourlyRate}
                  onChange={(e) => setHourlyRate(Number(e.target.value))}
                  min={0}
                  className="w-full border-3 border-kb-black px-4 py-3 font-mono font-bold text-base bg-kb-white focus:outline-none focus:shadow-brutal-sm focus:bg-kb-lavender transition-all duration-75"
                />
              </div>

              <div className="border-t-2 border-kb-black pt-4">
                <div className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black/50 mb-4">
                  WASTE SCORE WEIGHTS — MUST SUM TO 1.00
                </div>

                {[
                  {
                    label: 'COST FACTOR', value: costWeight, set: setCostWeight, color: 'bg-kb-peach',
                    desc: 'How heavily meeting size × duration weighs in the waste score. Increase if large expensive meetings are your main problem.',
                  },
                  {
                    label: 'DECISION DEFICIT', value: decisionWeight, set: setDecisionWeight, color: 'bg-kb-lavender',
                    desc: 'Penalty for meetings with no recorded decisions or outcomes. Increase this if inconclusive meetings are your biggest issue.',
                  },
                  {
                    label: 'PARTICIPATION', value: participationWeight, set: setParticipationWeight, color: 'bg-kb-mint',
                    desc: 'Penalty for over-attended meetings where most people are passive observers. Increase if you see too many unnecessary invites.',
                  },
                  {
                    label: 'RECURRENCE', value: recurrenceWeight, set: setRecurrenceWeight, color: 'bg-kb-pink',
                    desc: 'Penalty for recurring meetings that have grown stale over time (declining attendance, no outcomes). Needs 6+ months of data.',
                  },
                ].map(({ label, value, set, color, desc }) => (
                  <div key={label} className="mb-4">
                    <div className="flex items-center justify-between mb-1">
                      <label className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                        {label}
                      </label>
                      <span className={`${color} border-2 border-kb-black px-2 py-0.5 font-mono font-bold text-xs`}>
                        {value.toFixed(2)}
                      </span>
                    </div>
                    <p className="font-sans text-xs text-kb-black/50 mb-1">{desc}</p>
                    <input
                      type="range"
                      min="0"
                      max="1"
                      step="0.01"
                      value={value}
                      onChange={(e) => set(Number(e.target.value))}
                      className="w-full accent-kb-black"
                    />
                  </div>
                ))}

                <div className={`flex items-center justify-between border-t-2 border-kb-black pt-3 mt-2`}>
                  <span className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">TOTAL</span>
                  <span
                    className={`${weightsValid ? 'bg-kb-mint' : 'bg-kb-coral'} border-2 border-kb-black px-3 py-1 font-mono font-black text-sm`}
                  >
                    {weightSum.toFixed(2)}
                  </span>
                </div>
                {!weightsValid && (
                  <p className="font-mono text-xs text-kb-coral mt-1 uppercase">
                    Adjust weights to sum to exactly 1.00
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Ollama status */}
          <div className="flex items-center gap-2 px-4 py-3 bg-kb-white border-2 border-kb-black">
            <div className={`w-2 h-2 rounded-full flex-shrink-0 ${ollamaConnected ? 'bg-kb-mint' : 'bg-kb-coral'}`} />
            <span className="font-mono text-xs uppercase tracking-widest text-kb-black/60">
              OLLAMA: {ollamaConnected ? 'CONNECTED' : 'OFFLINE'}
            </span>
          </div>

          {/* Analyze button */}
          <button
            onClick={handleAnalyze}
            disabled={!weightsValid || isAnalyzing}
            className="w-full border-3 border-kb-black bg-kb-black text-kb-white shadow-brutal-md py-5 font-mono font-black text-xl uppercase tracking-widest hover:bg-kb-lavender hover:text-kb-black hover:translate-x-[3px] hover:translate-y-[3px] hover:shadow-brutal-none transition-all duration-75 disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-x-0 disabled:hover:translate-y-0 disabled:hover:shadow-brutal-md disabled:hover:bg-kb-black disabled:hover:text-kb-white"
          >
            {isAnalyzing ? 'ANALYZING...' : 'ANALYZE →'}
          </button>

          {Object.keys(transcripts).length > 0 && (
            <div className="bg-kb-lavender border-2 border-kb-black px-4 py-3">
              <p className="font-mono font-bold text-xs uppercase tracking-widest text-kb-black">
                {Object.keys(transcripts).length} TRANSCRIPT{Object.keys(transcripts).length !== 1 ? 'S' : ''} INCLUDED
              </p>
              <p className="font-mono text-xs text-kb-black/60 mt-1">
                Action items & decisions will be extracted via LLM
              </p>
            </div>
          )}

          {error && (
            <div className="bg-kb-coral border-3 border-kb-black p-4 shadow-brutal-sm">
              <p className="font-sans font-bold text-sm uppercase tracking-wide text-kb-black">
                ⚠ {error}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Made with Bob
