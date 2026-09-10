/**
 * ErrorBoundary
 *
 * Catches React render-time errors so the app shows a recoverable screen
 * instead of a white page. Sentry/error-tracking hooks are stubbed via
 * the optional onError prop — Phase 4 will wire that to a real reporter.
 */
import { Component, type ErrorInfo, type ReactNode } from 'react';

interface Props {
  children: ReactNode;
  /** Custom fallback. Receives the error and a reset() callback. */
  fallback?: (error: Error, reset: () => void) => ReactNode;
  /** Hook for error reporting. Phase 4 will wire Sentry here. */
  onError?: (error: Error, info: ErrorInfo) => void;
}

interface State {
  error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    this.props.onError?.(error, info);
    // Always log so a developer can find it even without a reporter.

    console.error('[ErrorBoundary]', error, info);
  }

  reset = (): void => {
    this.setState({ error: null });
  };

  render() {
    if (this.state.error) {
      if (this.props.fallback) {
        return this.props.fallback(this.state.error, this.reset);
      }
      return <DefaultFallback error={this.state.error} onReset={this.reset} />;
    }
    return this.props.children;
  }
}

function DefaultFallback({ error, onReset }: { error: Error; onReset: () => void }) {
  const isDev = import.meta.env.DEV;
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-6">
      <div className="max-w-md w-full bg-white border border-gray-200 rounded-lg shadow-sm p-6 space-y-4">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Something went wrong</h2>
          <p className="text-sm text-gray-600 mt-1">
            The page hit an unexpected error. You can try again, or go back to the dashboard.
          </p>
        </div>
        {isDev && (
          <pre className="text-xs bg-gray-100 border border-gray-200 rounded p-3 overflow-auto max-h-64 text-red-700 whitespace-pre-wrap">
            {error.message}
            {'\n\n'}
            {error.stack}
          </pre>
        )}
        <div className="flex gap-2">
          <button
            type="button"
            onClick={onReset}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md bg-blue-600 text-white hover:bg-blue-700"
          >
            Try again
          </button>
          <button
            type="button"
            onClick={() => {
              window.location.href = '/dashboard';
            }}
            className="flex-1 px-4 py-2 text-sm font-medium rounded-md border border-gray-300 text-gray-700 hover:bg-gray-50"
          >
            Go to dashboard
          </button>
        </div>
      </div>
    </div>
  );
}
