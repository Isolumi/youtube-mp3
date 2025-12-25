'use client';

import { useState, useRef, useEffect } from 'react';

type JobStatus = 'pending' | 'downloading' | 'converting' | 'complete' | 'error';

interface Job {
  id: string;
  url: string;
  jobId: string | null;
  status: JobStatus;
  progress: number;
  title: string;
  author: string;
  customFilename: string;
  error: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function YouTubeDownloader() {
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [jobs, setJobs] = useState<Job[]>([]);
  const pollingIntervals = useRef<Map<string, NodeJS.Timeout>>(new Map());

  useEffect(() => {
    return () => {
      pollingIntervals.current.forEach((interval) => clearInterval(interval));
    };
  }, []);

  const isValidYouTubeUrl = (url: string): boolean => {
    const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(watch\?v=|shorts\/)|youtu\.be\/).+$/;
    return youtubeRegex.test(url);
  };

  const pollStatus = async (localId: string, jobId: string) => {
    try {
      const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
      if (!response.ok) return;

      const data = await response.json();

      setJobs((prev) =>
        prev.map((job) => {
          if (job.id !== localId) return job;

          const updated = {
            ...job,
            status: data.status,
            progress: data.progress || 0,
          };

          if (data.status === 'complete') {
            updated.title = data.title || 'Unknown Title';
            updated.author = data.author || 'Unknown Author';
            updated.customFilename = data.title || 'audio';

            const interval = pollingIntervals.current.get(localId);
            if (interval) {
              clearInterval(interval);
              pollingIntervals.current.delete(localId);
            }
          } else if (data.status === 'error') {
            updated.error = data.error || 'Download failed';

            const interval = pollingIntervals.current.get(localId);
            if (interval) {
              clearInterval(interval);
              pollingIntervals.current.delete(localId);
            }
          }

          return updated;
        })
      );
    } catch (error) {
      console.error('Polling error:', error);
    }
  };

  const handleAddToQueue = async () => {
    if (!youtubeUrl.trim()) return;
    if (!isValidYouTubeUrl(youtubeUrl)) return;

    const localId = crypto.randomUUID();
    const newJob: Job = {
      id: localId,
      url: youtubeUrl,
      jobId: null,
      status: 'pending',
      progress: 0,
      title: '',
      author: '',
      customFilename: '',
      error: '',
    };

    setJobs((prev) => [...prev, newJob]);
    setYoutubeUrl('');

    try {
      const response = await fetch(`${API_BASE_URL}/download`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url: newJob.url }),
      });

      if (!response.ok) {
        setJobs((prev) =>
          prev.map((job) =>
            job.id === localId
              ? { ...job, status: 'error', error: 'Failed to submit job' }
              : job
          )
        );
        return;
      }

      const data = await response.json();

      setJobs((prev) =>
        prev.map((job) => (job.id === localId ? { ...job, jobId: data.job_id } : job))
      );

      const interval = setInterval(() => {
        pollStatus(localId, data.job_id);
      }, 2000);

      pollingIntervals.current.set(localId, interval);
    } catch (error) {
      setJobs((prev) =>
        prev.map((job) =>
          job.id === localId
            ? { ...job, status: 'error', error: 'Connection failed' }
            : job
        )
      );
    }
  };

  const handleDownload = async (job: Job) => {
    if (!job.jobId) return;

    try {
      const response = await fetch(`${API_BASE_URL}/result/${job.jobId}`);
      if (!response.ok) return;

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${job.customFilename}.mp3`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Download error:', error);
    }
  };

  const handleDownloadAll = () => {
    jobs.filter((job) => job.status === 'complete').forEach((job) => {
      handleDownload(job);
    });
  };

  const handleRemove = (id: string) => {
    const interval = pollingIntervals.current.get(id);
    if (interval) {
      clearInterval(interval);
      pollingIntervals.current.delete(id);
    }
    setJobs((prev) => prev.filter((job) => job.id !== id));
  };

  const updateFilename = (id: string, filename: string) => {
    setJobs((prev) =>
      prev.map((job) => (job.id === id ? { ...job, customFilename: filename } : job))
    );
  };

  const completedJobs = jobs.filter((job) => job.status === 'complete');

  return (
    <div className="w-full max-w-4xl mx-auto p-6">
      <div className="text-center mb-8">
        <h1 className="text-5xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
          YouTube to MP3
        </h1>
      </div>

      <div className="bg-white/80 dark:bg-gray-800/80 backdrop-blur-sm rounded-2xl shadow-2xl border border-gray-200 dark:border-gray-700 p-8 space-y-6">
        <div className="flex gap-3">
          <input
            type="text"
            value={youtubeUrl}
            onChange={(e) => setYoutubeUrl(e.target.value)}
            placeholder="Paste YouTube URL..."
            className="flex-1 px-5 py-4 text-lg border-2 border-gray-200 dark:border-gray-600 rounded-xl focus:ring-4 focus:ring-blue-500/20 focus:border-blue-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 transition-all outline-none"
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                handleAddToQueue();
              }
            }}
          />
          <button
            onClick={handleAddToQueue}
            disabled={!youtubeUrl.trim() || !isValidYouTubeUrl(youtubeUrl)}
            className="bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-semibold py-4 px-8 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl disabled:shadow-none whitespace-nowrap"
          >
            Add to Queue
          </button>
        </div>

        {completedJobs.length > 0 && (
          <button
            onClick={handleDownloadAll}
            className="w-full bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-200 shadow-lg hover:shadow-xl"
          >
            Download All ({completedJobs.length})
          </button>
        )}

        {jobs.length > 0 && (
          <div className="space-y-4 mt-6">
            {jobs.map((job) => (
              <div
                key={job.id}
                className="bg-gray-50 dark:bg-gray-900/50 rounded-xl p-5 border border-gray-200 dark:border-gray-700"
              >
                {/* Job Header */}
                <div className="flex items-start justify-between mb-3">
                  <div className="flex-1 min-w-0">
                    {job.title ? (
                      <div>
                        <p className="font-semibold text-gray-900 dark:text-white truncate">
                          {job.title}
                        </p>
                        <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                          {job.author}
                        </p>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600 dark:text-gray-400 truncate">
                        {job.url}
                      </p>
                    )}
                  </div>
                  <button
                    onClick={() => handleRemove(job.id)}
                    className="ml-3 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Progress Bar */}
                {(job.status === 'downloading' || job.status === 'converting') && (
                  <div className="mb-3">
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2 overflow-hidden">
                      <div
                        className="h-full bg-gradient-to-r from-blue-500 via-purple-500 to-blue-500 bg-[length:200%_100%] animate-gradient rounded-full transition-all duration-500"
                        style={{ width: `${job.progress}%` }}
                      />
                    </div>
                    <div className="flex justify-between items-center mt-1">
                      <span className="text-xs text-gray-600 dark:text-gray-400">
                        {job.status === 'downloading' ? 'Downloading' : 'Converting'}
                      </span>
                      <span className="text-xs font-semibold text-gray-900 dark:text-white">
                        {job.progress.toFixed(0)}%
                      </span>
                    </div>
                  </div>
                )}

                {/* Error */}
                {job.status === 'error' && (
                  <div className="bg-red-50 dark:bg-red-900/20 border-l-4 border-red-500 p-3 rounded-r-lg">
                    <p className="text-sm font-medium text-red-700 dark:text-red-400">
                      {job.error}
                    </p>
                  </div>
                )}

                {/* Complete - Filename Input */}
                {job.status === 'complete' && (
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={job.customFilename}
                      onChange={(e) => updateFilename(job.id, e.target.value)}
                      placeholder="Filename..."
                      className="flex-1 px-4 py-2 border-2 border-gray-200 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-green-500/20 focus:border-green-500 bg-white dark:bg-gray-700 text-gray-900 dark:text-white placeholder-gray-400 transition-all outline-none"
                    />
                    <button
                      onClick={() => handleDownload(job)}
                      disabled={!job.customFilename.trim()}
                      className="bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-700 hover:to-emerald-700 disabled:from-gray-400 disabled:to-gray-400 disabled:cursor-not-allowed text-white font-semibold py-2 px-6 rounded-lg transition-all duration-200 shadow-md hover:shadow-lg disabled:shadow-none whitespace-nowrap"
                    >
                      Download
                    </button>
                  </div>
                )}

                {/* Pending */}
                {job.status === 'pending' && (
                  <div className="flex items-center gap-2 text-sm text-gray-600 dark:text-gray-400">
                    <div className="animate-spin rounded-full h-4 w-4 border-2 border-gray-300 border-t-blue-600"></div>
                    <span>Starting...</span>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}

        {jobs.length === 0 && (
          <div className="text-center py-12 text-gray-400 dark:text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            <p>No downloads yet. Add a YouTube URL to get started.</p>
          </div>
        )}
      </div>
    </div>
  );
}
