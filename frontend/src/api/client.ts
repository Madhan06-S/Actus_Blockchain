const BASE_URL = 'http://localhost:8000';

export async function fetchApi<T>(endpoint: string, options?: RequestInit): Promise<T> {
  const url = `${BASE_URL}${endpoint}`;
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ detail: response.statusText }));
      throw new Error(errorData.detail || `Request failed with status ${response.status}`);
    }

    return await response.json();
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Network error';
    throw new Error(message);
  }
}
