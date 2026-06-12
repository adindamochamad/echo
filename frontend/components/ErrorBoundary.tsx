"use client";

import React, { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
}

interface State {
  adaError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { adaError: false };
  }

  static getDerivedStateFromError(): State {
    return { adaError: true };
  }

  render() {
    if (this.state.adaError) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
          <span className="text-4xl">⚠️</span>
          <h2 className="text-lg font-semibold">Something went wrong</h2>
          <p className="text-slate-500 text-sm">Refresh the page to try again.</p>
          <button
            onClick={() => window.location.reload()}
            className="px-4 py-2 bg-navy text-white rounded-lg text-sm"
          >
            Refresh
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
