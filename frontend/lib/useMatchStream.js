"use client";

/*
  useMatchStream: the one place where the frontend talks to the backend.

  1. Opens a Server-Sent Events connection with EventSource("/stream?...").
  2. Listens for the message types the backend sends:
       start, event, stats, moment, insight, recap, end
  3. Each message updates a piece of state, and React redraws that part of the page.
  4. When the viewer changes mode / club / player / language, start() is called
     again with a new URL, so the old connection is closed and a new one opens.
*/

import { useCallback, useEffect, useRef, useState } from "react";

export const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EMPTY = {
  status: "idle", // idle | live | finished | error
  info: null,
  profile: null,
  events: [],
  stats: null,
  moments: [],
  insights: [],
  recap: null,
  score: null,
};

export function useMatchStream() {
  const [state, setState] = useState(EMPTY);
  const sourceRef = useRef(null);

  const stop = useCallback(() => {
    if (sourceRef.current) {
      sourceRef.current.close();
      sourceRef.current = null;
    }
  }, []);

  const start = useCallback(
    (options) => {
      stop();
      setState({ ...EMPTY, status: "live" });

      // Build the URL from the viewer's choices
      const params = new URLSearchParams();
      Object.entries(options).forEach(([key, value]) => {
        if (value !== null && value !== undefined && value !== "") params.set(key, value);
      });
      const source = new EventSource(`${API_URL}/stream?${params.toString()}`);
      sourceRef.current = source;

      // Small helper: listen for one message type and update state with it
      const on = (type, update) =>
        source.addEventListener(type, (message) => {
          const data = JSON.parse(message.data);
          setState((previous) => ({ ...previous, ...update(data, previous) }));
        });

      on("start", (data) => ({ info: data.info, profile: data.profile }));
      on("event", (data, prev) => ({ events: [...prev.events, data] }));
      on("stats", (data) => ({ stats: data }));
      on("moment", (data, prev) => ({ moments: [...prev.moments, data] }));
      on("insight", (data, prev) => ({ insights: [data, ...prev.insights] }));
      on("recap", (data) => ({ recap: data }));
      on("end", (data) => {
        source.close(); // otherwise the browser would reconnect and replay the match
        return { status: "finished", score: data.score };
      });

      source.onerror = () => {
        // EventSource fires an error when the server closes the stream or is down
        if (sourceRef.current === source) {
          source.close();
          setState((previous) =>
            previous.status === "live" ? { ...previous, status: "error" } : previous
          );
        }
      };
    },
    [stop]
  );

  useEffect(() => stop, [stop]); // close the connection when the page closes

  return { ...state, start, stop };
}
