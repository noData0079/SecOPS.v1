import React from 'react';

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <h1 className="text-4xl font-extrabold tracking-tight lg:text-5xl">
        Autonomous Security Intelligence
      </h1>
      <p className="mt-4 text-xl text-muted-foreground max-w-2xl">
        The sovereign AI platform for detecting, explaining, and fixing security risks at machine speed.
      </p>
      <div className="mt-8 flex gap-4">
        <a href="/dashboard" className="px-6 py-3 rounded-md bg-slate-900 text-white font-medium hover:bg-slate-800">
          Get Started
        </a>
        <a href="/docs" className="px-6 py-3 rounded-md bg-white text-slate-900 border border-slate-200 font-medium hover:bg-slate-50">
          Read Documentation
        </a>
      </div>
    </div>
  );
}
