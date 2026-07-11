import { Page } from '@playwright/test';

export interface ConsoleError {
  type: 'error' | 'warning';
  message: string;
  location?: string;
}

export interface NetworkError {
  url: string;
  method: string;
  status: number;
  statusText: string;
}

// URLs whose failures are environment-specific and not real app bugs
const IGNORED_URL_PATTERNS = [
  /fonts\.googleapis\.com/,
  /fonts\.gstatic\.com/,
  /unsplash\.com/,
  /images\.unsplash\.com/,
  /analytics/,
  /gtag/,
  /_next\/image/,
  /hot-update/,
];

// Console messages to ignore (Next.js dev noise, browser extensions, etc.)
const IGNORED_CONSOLE_PATTERNS = [
  /Download the React DevTools/,
  /Each child in a list/,
  /Warning.*fill.*sizes/,           // Next.js Image sizes warning
  /sizes.*fill/,
  /_next\/image/,                   // Image optimization errors
  /Failed to load resource.*_next\/image/,
  /Image.*fill.*missing.*sizes/,
  /Read more: https:\/\/nextjs\.org.*image/,
];

export class ErrorCollector {
  private consoleErrors: ConsoleError[] = [];
  private networkErrors: NetworkError[] = [];

  constructor(private page: Page) {}

  async start() {
    this.page.on('console', (msg) => {
      if (msg.type() !== 'error' && msg.type() !== 'warning') return;
      const text = msg.text();
      if (IGNORED_CONSOLE_PATTERNS.some((p) => p.test(text))) return;
      this.consoleErrors.push({
        type: msg.type() as 'error' | 'warning',
        message: text,
        location: msg.location()
          ? `${msg.location().url}:${msg.location().lineNumber}`
          : undefined,
      });
    });

    this.page.on('pageerror', (error) => {
      // Skip errors that are from ignored origins
      if (IGNORED_CONSOLE_PATTERNS.some((p) => p.test(error.message))) return;
      this.consoleErrors.push({ type: 'error', message: error.message });
    });

    this.page.on('response', (response) => {
      if (response.status() < 400) return;
      const url = response.url();
      if (IGNORED_URL_PATTERNS.some((p) => p.test(url))) return;
      this.networkErrors.push({
        url,
        method: response.request().method(),
        status: response.status(),
        statusText: response.statusText(),
      });
    });

    this.page.on('requestfailed', (request) => {
      const url = request.url();
      if (IGNORED_URL_PATTERNS.some((p) => p.test(url))) return;
      this.networkErrors.push({
        url,
        method: request.method(),
        status: 0,
        statusText: request.failure()?.errorText || 'Request failed',
      });
    });
  }

  getErrors() {
    return { console: this.consoleErrors, network: this.networkErrors };
  }

  printErrors() {
    if (this.consoleErrors.length)
      console.log('\nConsole errors:', JSON.stringify(this.consoleErrors, null, 2));
    if (this.networkErrors.length)
      console.log('\nNetwork errors:', JSON.stringify(this.networkErrors, null, 2));
  }
}
