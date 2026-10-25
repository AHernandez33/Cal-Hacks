/** Wait for decoded pixels rather than treating stream permission as a frame. */
export function waitForCameraFrame(video: HTMLVideoElement, signal: AbortSignal) {
  return new Promise<void>((resolve, reject) => {
    const events = ["loadeddata", "playing", "canplay", "resize"];
    const cleanup = () => {
      clearTimeout(timeout);
      clearInterval(interval);
      events.forEach(event => video.removeEventListener(event, check));
      signal.removeEventListener("abort", abort);
    };
    const abort = () => {
      cleanup();
      reject(new DOMException("Camera opening cancelled.", "AbortError"));
    };
    const check = () => {
      if (video.readyState >= HTMLMediaElement.HAVE_CURRENT_DATA &&
          video.videoWidth > 0 && video.videoHeight > 0 && !video.paused) {
        cleanup();
        resolve();
      }
    };
    const timeout = setTimeout(() => {
      cleanup();
      reject(new Error("The camera opened but sent no picture. Close other camera apps, reconnect the webcam, and try again."));
    }, 12000);
    const interval = setInterval(check, 100);
    events.forEach(event => video.addEventListener(event, check));
    signal.addEventListener("abort", abort, {once: true});
    if (signal.aborted) abort();
    else check();
  });
}

export function cameraError(error: unknown): string {
  if (error instanceof DOMException) {
    if (["NotAllowedError", "SecurityError"].includes(error.name))
      return "Camera access was blocked. Allow camera access in your browser and Windows camera privacy settings, then try again.";
    if (["NotReadableError", "AbortError"].includes(error.name))
      return "The camera could not start. Close other apps using it (such as Teams or Zoom), reconnect it, and try again.";
    if (["NotFoundError", "OverconstrainedError"].includes(error.name))
      return "The selected camera is unavailable. Connect a webcam or choose another camera device.";
  }
  return error instanceof Error ? error.message : "Camera unavailable.";
}

export async function captureCameraFrame(video: HTMLVideoElement) {
  if (video.readyState < HTMLMediaElement.HAVE_CURRENT_DATA || !video.videoWidth || !video.videoHeight)
    throw new Error("The camera has no picture yet. Wait for the live preview before capturing.");
  // Bound camera uploads independently of the webcam's native resolution.
  const scale = Math.min(1, 1920 / Math.max(video.videoWidth, video.videoHeight));
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(video.videoWidth * scale));
  canvas.height = Math.max(1, Math.round(video.videoHeight * scale));
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("This browser could not create a camera picture. Try uploading a photo instead.");
  ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
  const blob = await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob(value => value ? resolve(value) : reject(new Error("The browser could not save this camera frame. Try again.")), "image/jpeg", 0.85);
  });
  return {blob, width: canvas.width, height: canvas.height};
}
