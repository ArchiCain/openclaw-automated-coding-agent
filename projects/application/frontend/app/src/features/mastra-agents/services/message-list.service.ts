import { Injectable, inject, OnDestroy } from '@angular/core';
import { BehaviorSubject, Subscription } from 'rxjs';
import { WebSocketService } from '../../api-client/websocket.service';
import { Conversation } from '../types';
import { ChatService } from './chat.service';

const HISTORY_NAMESPACE = '/mastra-chat-history';

@Injectable({ providedIn: 'root' })
export class MessageListService implements OnDestroy {
  private ws = inject(WebSocketService);
  private chatService = inject(ChatService);

  conversations$ = new BehaviorSubject<Conversation[]>([]);

  private subscriptions = new Subscription();

  loadConversations(): void {
    this.ws.connect(HISTORY_NAMESPACE);

    this.subscriptions.add(
      this.ws.on<Conversation[]>(HISTORY_NAMESPACE, 'conversations').subscribe(conversations => {
        this.conversations$.next(conversations);
      })
    );

    this.ws.emit(HISTORY_NAMESPACE, 'get-conversations', {});
  }

  selectConversation(threadId: string): void {
    this.chatService.currentThreadId$.next(threadId);
    this.chatService.clearMessages();
    this.ws.emit(HISTORY_NAMESPACE, 'get-messages', { threadId });

    this.subscriptions.add(
      this.ws.on<{ messages: import('../types').ChatMessage[] }>(HISTORY_NAMESPACE, 'messages').subscribe(({ messages }) => {
        this.chatService.messages$.next(messages);
      })
    );
  }

  ngOnDestroy(): void {
    this.subscriptions.unsubscribe();
    this.ws.disconnect(HISTORY_NAMESPACE);
  }
}
