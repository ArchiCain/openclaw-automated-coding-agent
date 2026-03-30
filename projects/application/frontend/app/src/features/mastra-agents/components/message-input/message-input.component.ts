import { Component, EventEmitter, Output, inject } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { MatFormFieldModule } from '@angular/material/form-field';
import { MatInputModule } from '@angular/material/input';
import { MatButtonModule } from '@angular/material/button';
import { MatIconModule } from '@angular/material/icon';
import { AsyncPipe } from '@angular/common';
import { ChatService } from '../../services/chat.service';

@Component({
  selector: 'app-message-input',
  standalone: true,
  imports: [FormsModule, MatFormFieldModule, MatInputModule, MatButtonModule, MatIconModule, AsyncPipe],
  template: `
    <div class="message-input-container">
      <mat-form-field appearance="outline" class="message-field">
        <textarea
          matInput
          placeholder="Type a message..."
          [(ngModel)]="messageText"
          (keydown.control.enter)="send()"
          rows="2"
        ></textarea>
      </mat-form-field>
      <button
        mat-icon-button
        aria-label="Send"
        [disabled]="!messageText.trim() || (chatService.isStreaming$ | async)"
        (click)="send()"
      >
        <mat-icon>send</mat-icon>
      </button>
    </div>
  `,
  styles: [`
    .message-input-container {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 8px 16px;
    }
    .message-field {
      flex: 1;
    }
  `],
})
export class MessageInputComponent {
  @Output() messageSent = new EventEmitter<string>();

  chatService = inject(ChatService);
  messageText = '';

  send(): void {
    const text = this.messageText.trim();
    if (!text) return;
    this.messageSent.emit(text);
    this.messageText = '';
  }
}
