import { useState, useEffect, useCallback, DependencyList } from 'react';

type QueryResult<T> = {
  data: T | null;
  isLoading: boolean;
  isError: boolean;
};

function useQuery<T>(
  queryFn: () => Promise<T>,
  deps: DependencyList = []
): QueryResult<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isError, setIsError] = useState<boolean>(false);

  const memoizedQueryFn = useCallback(queryFn, deps);

  useEffect(() => {
    let isMounted = true;
    const fetchData = async () => {
      setIsLoading(true);
      setIsError(false);
      try {
        const result = await memoizedQueryFn();
        if (isMounted) {
          setData(result);
        }
      } catch (err) {
        if (isMounted) {
          setIsError(true);
          console.error('An error occurred while fetching data:', err);
        }
      } finally {
        if (isMounted) {
          setIsLoading(false);
        }
      }
    };

    fetchData();

    return () => {
      isMounted = false;
    };
  }, [memoizedQueryFn]);

  return { data, isLoading, isError };
}

export default useQuery;