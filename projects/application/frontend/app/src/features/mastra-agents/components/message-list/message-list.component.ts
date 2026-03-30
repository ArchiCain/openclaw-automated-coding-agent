import { Component, inject, OnInit, AfterViewChecked, ElementRef, ViewChild } from '@angular/core';
import { AsyncPipe, NgFor, NgIf } from '@angular/common';
import { MarkdownComponent } from 'ngx-markdown';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-message-list',
  standalone: true,
  imports: [AsyncPipe, NgFor, NgIf, MarkdownComponent],
  template: `
    <div class="message-list" #scrollContainer>
      <ng-container *ngFor="let message of chatService.messages$ | async">
        <article
          *ngIf="message.role === 'assistant'"
          role="article"
          aria-label="Assistant message"
          class="message message--assistant"
        >
          <markdown [data]="message.content"></markdown>
          <span *ngIf="message.isStreaming" class="streaming-indicator" aria-label="Streaming">...</span>
        </article>
        <article *ngIf="message.role === 'user'" class="message message--user">
          {{ message.content }}
        </article>
      </ng-container>
      <div *ngIf="chatService.isStreaming$ | async" class="streaming-indicator-wrapper">
        <span class="streaming-dots">Thinking...</span>
      </div>
    </div>
  `,
  styles: [`
    .message-list {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }
    .message {
      padding: 12px 16px;
      border-radius: 8px;
      max-width: 80%;
    }
    .message--user {
      align-self: flex-end;
      background-color: var(--mat-sys-primary-container, #e3f2fd);
    }
    .message--assistant {
      align-self: flex-start;
      background-color: var(--mat-sys-surface-variant, #f5f5f5);
    }
    .streaming-indicator {
      opacity: 0.6;
      animation: blink 1s infinite;
    }
    .streaming-indicator-wrapper {
      align-self: flex-start;
      padding: 8px 16px;
      opacity: 0.7;
    }
    @keyframes blink {
      0%, 100% { opacity: 0.3; }
      50% { opacity: 1; }
    }
  `],
})
export class MessageListComponent implements AfterViewChecked {
  @ViewChild('scrollContainer') private scrollContainer!: ElementRef<HTMLElement>;

  chatService = inject(ChatService);

  ngAfterViewChecked(): void {
    this.scrollToBottom();
  }

  private scrollToBottom(): void {
    if (this.scrollContainer) {
      const el = this.scrollContainer.nativeElement;
      el.scrollTop = el.scrollHeight;
    }
  }
}
