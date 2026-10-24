export type Observation = {
  id: string;
  createdAt: string;
  name: string;
  photo: Blob;
  queued?: boolean;
  lastError?: string;
};
const DB_NAME = "vigilo-local-observations";
const STORE = "photos";
function openDB(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, 1);
    req.onupgradeneeded = () => {
      if (!req.result.objectStoreNames.contains(STORE))
        req.result.createObjectStore(STORE, { keyPath: "id" });
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}
async function mutate(action: (store: IDBObjectStore) => void) {
  const db = await openDB();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(STORE, "readwrite");
      action(tx.objectStore(STORE));
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () =>
        reject(tx.error || new Error("Storage transaction aborted"));
    });
  } finally {
    db.close();
  }
}
export async function saveObservation(photo: Blob, name: string) {
  if (photo.size > 8 * 1024 * 1024) throw new Error("Photo exceeds 8 MiB.");
  const entry: Observation = {
    id: crypto.randomUUID(),
    createdAt: new Date().toISOString(),
    name,
    photo,
    queued: false,
  };
  await mutate((store) => {
    store.put(entry);
  });
  return entry.id;
}
export async function listObservations(): Promise<Observation[]> {
  const db = await openDB();
  try {
    return await new Promise<Observation[]>((resolve, reject) => {
      const tx = db.transaction(STORE);
      const req = tx.objectStore(STORE).getAll();
      req.onsuccess = () =>
        resolve(
          req.result.sort((a: Observation, b: Observation) =>
            b.createdAt.localeCompare(a.createdAt),
          ),
        );
      req.onerror = () => reject(req.error);
    });
  } finally {
    db.close();
  }
}
export async function deleteObservation(id: string) {
  await mutate((store) => {
    store.delete(id);
  });
}
export async function setQueued(id: string, queued: boolean, lastError = "") {
  await mutate((store) => {
    const req = store.get(id);
    req.onsuccess = () => {
      if (req.result) store.put({ ...req.result, queued, lastError });
    };
  });
}
