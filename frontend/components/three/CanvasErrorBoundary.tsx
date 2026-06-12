"use client";

import { Component, ReactNode } from "react";

interface Props {
  children: ReactNode;
  variant: string;
}

interface State {
  gagal: boolean;
}

/** Tangkap error WebGL/R3F — fallback ke gradient statis */
export class CanvasErrorBoundary extends Component<Props, State> {
  state: State = { gagal: false };

  static getDerivedStateFromError(): State {
    return { gagal: true };
  }

  render() {
    if (this.state.gagal) {
      return (
        <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50 to-slate-100" />
      );
    }
    return this.props.children;
  }
}
