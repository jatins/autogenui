import * as service from './client/services.gen';
import fetchDataSC from './fetchDataSC';

export default async function Home() {
  const { data, error } = await fetchDataSC(() => service.getItemsItemsGet());

  if (error) {
    return <div>Error: {error.message}</div>;
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      {data ? (
        <pre>{JSON.stringify(data, null, 2)}</pre>
      ) : (
        "No data available"
      )}
    </main>
  );
}