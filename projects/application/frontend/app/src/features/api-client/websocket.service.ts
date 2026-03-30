import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';
import { io, Socket } from 'socket.io-client';
import { BackendConfigService } from '../backend-selector/backend-config.service';

@Injectable({ providedIn: 'root' })
export class WebSocketService {
  private sockets = new Map<string, Socket>();
  private backendConfig = inject(BackendConfigService);

  connect(namespace: string): void {
    if (this.sockets.has(namespace)) {
      return;
    }
    const baseUrl = this.backendConfig.getBaseUrl();
    const socketUrl = baseUrl ? `${baseUrl}${namespace}` : namespace;
    const socket = io(socketUrl, { withCredentials: true });
    this.sockets.set(namespace, socket);
  }

  disconnect(namespace: string): void {
    const socket = this.sockets.get(namespace);
    if (socket) {
      socket.disconnect();
      this.sockets.delete(namespace);
    }
  }

  emit(namespace: string, event: string, data: unknown): void {
    const socket = this.sockets.get(namespace);
    if (socket) {
      socket.emit(event, data);
    }
  }

  on<T>(namespace: string, event: string): Observable<T> {
    return new Observable<T>(observer => {
      const socket = this.sockets.get(namespace);
      if (!socket) {
        observer.error(new Error(`No socket connected for namespace: ${namespace}`));
        return;
      }
      const handler = (data: T) => observer.next(data);
      socket.on(event, handler);
      return () => socket.off(event, handler);
    });
  }
}
