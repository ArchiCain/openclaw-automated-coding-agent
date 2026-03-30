import { Component, OnInit, inject } from '@angular/core';
import { MessageListComponent } from '../components/message-list/message-list.component';
import { MessageInputComponent } from '../components/message-input/message-input.component';
import { ChatHistorySidebarComponent } from '../components/chat-history-sidebar/chat-history-sidebar.component';
import { ChatService } from '../services/chat.service';
import { MessageListService } from '../services/message-list.service';

const DEFAULT_AGENT_ID = 'default';

@Component({
  selector: 'app-chat-page',
  standalone: true,
  imports: [MessageListComponent, MessageInputComponent, ChatHistorySidebarComponent],
  template: `
    <div class="chat-layout">
      <aside class="chat-sidebar">
        <app-chat-history-sidebar />
      </aside>
      <main class="chat-main">
        <app-message-list class="chat-messages" />
        <app-message-input (messageSent)="onMessageSent($event)" />
      </main>
    </div>
  `,
  styles: [`
    .chat-layout {
      display: flex;
      height: 100%;
      overflow: hidden;
    }
    .chat-sidebar {
      width: 260px;
      flex-shrink: 0;
      border-right: 1px solid var(--mat-sys-outline-variant, #e0e0e0);
      overflow-y: auto;
    }
    .chat-main {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    app-message-list {
      flex: 1;
      overflow: hidden;
    }
  `],
})
export class ChatPage implements OnInit {
  private chatService = inject(ChatService);
  private messageListService = inject(MessageListService);

  ngOnInit(): void {
    this.chatService.initialize();
    this.messageListService.loadConversations();
  }

  onMessageSent(text: string): void {
    this.chatService.sendMessage(text, DEFAULT_AGENT_ID);
  }
}
