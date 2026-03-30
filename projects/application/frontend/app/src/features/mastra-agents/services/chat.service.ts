import { Injectable, inject, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subscription } from 'rxjs';
import { WebSocketService } from '../../api-client/websocket.service';
import { ChatMessage } from '../types';

const CHAT_NAMESPACE = '/mastra-chat';

@Injectable({ providedIn: 'root' })
export class ChatService implements OnDestroy {
  private ws = inject(WebSocketService);

  messages$ = new BehaviorSubject<ChatMessage[]>([]);
  isStreaming$ = new BehaviorSubject<boolean>(false);
  currentThreadId$ = new BehaviorSubject<string | null>(null);

  private subscriptions = new Subscription();

  initialize(): void {
    this.ws.connect(CHAT_NAMESPACE);

    this.subscriptions.add(
      this.ws.on<{ content: string; threadId: string }>(CHAT_NAMESPACE, 'chat-chunk').subscribe(({ content, threadId }) => {
        const messages = this.messages$.getValue();
        const last = messages[messages.length - 1];

        if (last && last.role === 'assistant' && last.isStreaming) {
          const updated = { ...last, content: last.content + content };
          this.messages$.next([...messages.slice(0, -1), updated]);
        } else {
          const streamingMsg: ChatMessage = {
            id: `streaming-${threadId}`,
            role: 'assistant',
            content,
            timestamp: new Date(),
            isStreaming: true,
          };
          this.messages$.next([...messages, streamingMsg]);
        }

        if (this.currentThreadId$.getValue() === null) {
          this.currentThreadId$.next(threadId);
        }
      })
    );

    this.subscriptions.add(
      this.ws.on<{ threadId: string }>(CHAT_NAMESPACE, 'chat-complete').subscribe(() => {
        const messages = this.messages$.getValue();
        const last = messages[messages.length - 1];
        if (last && last.isStreaming) {
          const finalized = { ...last, isStreaming: false };
          this.messages$.next([...messages.slice(0, -1), finalized]);
        }
        this.isStreaming$.next(false);
      })
    );

    this.subscriptions.add(
      this.ws.on<{ error: string }>(CHAT_NAMESPACE, 'chat-error').subscribe(({ error }) => {
        const errorMsg: ChatMessage = {
          id: `error-${Date.now()}`,
          role: 'assistant',
          content: error,
          timestamp: new Date(),
        };
        this.messages$.next([...this.messages$.getValue(), errorMsg]);
        this.isStreaming$.next(false);
      })
    );
  }

  sendMessage(text: string, agentId: string): void {
    const userMsg: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    this.messages$.next([...this.messages$.getValue(), userMsg]);
    this.isStreaming$.next(true);

    this.ws.emit(CHAT_NAMESPACE, 'chat-message', {
      message: text,
      agentId,
      threadId: this.currentThreadId$.getValue() ?? undefined,
    });
  }

  clearMessages(): void {
    this.messages$.next([]);
    this.currentThreadId$.next(null);
    this.isStreaming$.next(false);
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.ws.disconnect(CHAT_NAMESPACE);
  }
}
