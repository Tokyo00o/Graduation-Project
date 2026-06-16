import { useEffect, useRef, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';

interface WSMessage {
  type: 'iteration' | 'status' | 'metrics' | 'tree_snapshot' | 'pong';
  data: any;
}

const RECONNECT_DELAY = 3000;

export function useJobWebSocket(jobId: string | undefined) {
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>();
  const [connected, setConnected] = useState(false);
  const [liveIterations, setLiveIterations] = useState<any[]>([]);
  const [treeSnapshot, setTreeSnapshot] = useState<any>(null);
  const qc = useQueryClient();

  const connect = () => {
    if (!jobId) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const url = `${protocol}//${window.location.host}/api/v1/ws/jobs/${jobId}`;

    const socket = new WebSocket(url);
    ws.current = socket;

    socket.onopen = () => setConnected(true);

    socket.onmessage = (event) => {
      const msg: WSMessage = JSON.parse(event.data);

      switch (msg.type) {
        case 'iteration':
          setLiveIterations((prev) => [msg.data, ...prev.slice(0, 49)]);
          break;
        case 'status':
          qc.setQueryData(['job', jobId], (old: any) => {
            if (!old) return old;
            return { ...old, ...msg.data };
          });
          break;
        case 'metrics':
          qc.setQueryData(['metrics', jobId], (old: any) => {
            if (!old) return old;
            return { ...old, ...msg.data };
          });
          break;
        case 'tree_snapshot':
          setTreeSnapshot(msg.data);
          break;
      }
    };

    socket.onclose = () => {
      setConnected(false);
      ws.current = null;
      reconnectTimer.current = setTimeout(connect, RECONNECT_DELAY);
    };

    socket.onerror = () => {
      socket.close();
    };
  };

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      ws.current?.close();
      setLiveIterations([]);
      setConnected(false);
    };
  }, [jobId]);

  return { connected, liveIterations, treeSnapshot };
}
