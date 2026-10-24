import { listObservations, setQueued } from "./offline_storage";
import { requestJSON, type PrivacySettings, type VisionResponse } from "./api";
export async function synchronizeQueue(
  explicitPermission: boolean,
  onAnalyzed?: (value: VisionResponse) => void,
) {
  if (!explicitPermission)
    throw new Error("Explicit synchronization permission is required.");
  const settings = await requestJSON<PrivacySettings>("/privacy/settings");
  if (!settings.observation_sync_enabled)
    throw new Error(
      "Enable observation synchronization in Privacy settings first.",
    );
  let completed = 0;
  const errors: string[] = [];
  for (const observation of (await listObservations()).filter(
    (item) => item.queued,
  )) {
    const form = new FormData();
    form.append(
      "file",
      observation.photo,
      observation.photo.type === "image/png" ? "leaf.png" : "leaf.jpg",
    );
    try {
      const value = await requestJSON<{ analysis: VisionResponse }>(
        "/observations/sync?authorize_sync=true",
        { method: "POST", body: form },
      );
      await setQueued(observation.id, false);
      completed++;
      onAnalyzed?.(value.analysis);
    } catch (e) {
      const error = String(e);
      await setQueued(observation.id, true, error);
      errors.push(`${observation.name}: ${error}`);
      break;
    }
  }
  return { completed, errors };
}
