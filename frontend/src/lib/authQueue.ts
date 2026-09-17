/* eslint-disable @typescript-eslint/no-explicit-any, @typescript-eslint/no-unused-vars */
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function subscribeTokenRefresh(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

function onReroute(token: string) {
  refreshSubscribers.forEach((cb) => cb(token));
  refreshSubscribers = [];
}

export async function runRefresh(refreshFn: (refreshToken: string) => Promise<any>): Promise<string> {
  const refreshToken = localStorage.getItem('refresh_token');
  if (!refreshToken) {
    localStorage.clear();
    window.location.href = '/login';
    throw new Error('No refresh token');
  }

  if (isRefreshing) {
    return new Promise((resolve) => {
      subscribeTokenRefresh((token: string) => {
        resolve(token);
      });
    });
  }

  isRefreshing = true;

  try {
    const res = await refreshFn(refreshToken);
    const newToken = typeof res === 'string' ? res : res.access_token;
    localStorage.setItem('access_token', newToken);
    isRefreshing = false;
    onReroute(newToken);
    return newToken;
  } catch (err) {
    isRefreshing = false;
    localStorage.clear();
    window.location.href = '/login';
    throw err;
  }
}
