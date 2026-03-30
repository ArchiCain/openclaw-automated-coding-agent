import { Component, inject } from '@angular/core';
import { AsyncPipe, NgFor } from '@angular/common';
import { MatListModule } from '@angular/material/list';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { MessageListService } from '../../services/message-list.service';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-chat-history-sidebar',
  standalone: true,
  imports: [AsyncPipe, NgFor, MatListModule, MatButtonModule, MatIconModule],
  template: `
    <div class="sidebar">
      <div class="sidebar-header">
        <button mat-stroked-button (click)="newChat()">
          <mat-icon>add</mat-icon>
          New Chat
        </button>
      </div>
      <mat-nav-list>
        <mat-list-item
          *ngFor="let conversation of messageListService.conversations$ | async"
          (click)="messageListService.selectConversation(conversation.threadId)"
        >
          {{ conversation.title }}
        </mat-list-item>
      </mat-nav-list>
    </div>
  `,
  styles: [`
    .sidebar {
      display: flex;
      flex-direction: column;
      height: 100%;
      overflow: hidden;
    }
    .sidebar-header {
      padding: 16px;
      border-bottom: 1px solid var(--mat-sys-outline-variant, #e0e0e0);
    }
  `],
})
export class ChatHistorySidebarComponent {
  messageListService = inject(MessageListService);
  private chatService = inject(ChatService);

  newChat(): void {
    this.chatService.clearMessages();
  }
}
