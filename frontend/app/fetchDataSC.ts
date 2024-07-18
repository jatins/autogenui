import { cache } from 'react';

type QueryResult<T> = {
  data: T | null;
  error: Error | null;
};

async function fetchDataSC<T>(
  queryFn: () => Promise<T>
): Promise<QueryResult<T>> {
  const cachedQueryFn = cache(queryFn);

  try {
    const data = await cachedQueryFn();
    return { data, error: null };
  } catch (error) {
    console.error('An error occurred while fetching data:', error);
    return { data: null, error: error instanceof Error ? error : new Error(String(error)) };
  }
}

export default fetchDataSC;