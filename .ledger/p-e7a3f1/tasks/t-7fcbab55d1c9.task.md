---
id: t-7fcbab55d1c9
planId: p-e7a3f1
project: frontend
feature: chat
specialist: frontend-eng
dependsOn: ["t-9c0ec2c1931d", "t-c06bdcef4e32"]
status: ready
attempts: 0
commitHash: null
created: 2026-03-29T18:27:00.000Z
updated: 2026-03-29T18:27:00.000Z
---

# Task: Chat UI Components and Chat Page

## Goal
Build the chat UI components for the `mastra-agents` feature: the message list, message input, chat history sidebar, and the root chat page component. This creates the full conversational AI interface using Angular Material and `ngx-markdown` for rendered message content.

## Context
The existing React implementation: `projects/application/frontend/app/src/features/mastra-agents/pages/ConversationalAI.tsx` (chat page), `chat/MastraChat.tsx` (chat container), `chat/message-list/` (message rendering), `chat/message-input/` (input bar), `MastraChatWithSidebar.tsx` (sidebar layout). The Angular version uses `ngx-markdown` for markdown rendering with syntax highlighting.

`ChatService` and `MessageListService` are in the dependency task (t-9c0ec2c1931d).

**Important for E2E compatibility**:
- Message input: `getByPlaceholder(/type.*message/i)` or similar placeholder text
- Send button: `getByRole('button', { name: /send/i })`
- Assistant messages: `getByRole('article', { name: /assistant message/i })`

## What to Build

Extend `src/features/mastra-agents/` with:

- `components/message-input/message-input.component.ts` — standalone:
  - `<mat-form-field>`, `<textarea matInput placeholder="Type a message...">` + Send button
  - `@Output() messageSent = new EventEmitter<string>()`
  - Send on button click or Ctrl+Enter; disabled while `ChatService.isStreaming$` is true
  - Send button: `<button mat-icon-button aria-label="Send"><mat-icon>send</mat-icon></button>` with visible "Send" label or `aria-label="Send"`
- `components/message-list/message-list.component.ts` — standalone:
  - Renders `ChatService.messages$` list
  - Each assistant message: `<article role="article" aria-label="Assistant message">` with `<markdown [data]="message.content">` (ngx-markdown)
  - Each user message: simple text display
  - Streaming indicator for the last message when `isStreaming$` is true
  - Auto-scrolls to bottom on new messages
- `components/chat-history-sidebar/chat-history-sidebar.component.ts` — standalone:
  - Lists `MessageListService.conversations$`
  - Each item: clickable `<mat-list-item>` that calls `MessageListService.selectConversation()`
  - "New Chat" button
- `pages/chat.page.ts` — standalone routed component (replaces `ConversationalAI.tsx`):
  - Composes `MessageListComponent`, `MessageInputComponent`, `ChatHistorySidebarComponent`
  - Calls `ChatService.initialize()` on init
  - Calls `ChatService.sendMessage()` when `messageSent` fires

## Acceptance Criteria
- [ ] Message input has `placeholder` matching `/type.*message/i`
- [ ] Send button has accessible "Send" name/label
- [ ] Assistant messages are in `<article>` elements with `aria-label="Assistant message"`
- [ ] `ngx-markdown` renders markdown in assistant messages
- [ ] Streaming indicator shown during `isStreaming$` = true
- [ ] All components are standalone
- [ ] `ng build` succeeds
- [ ] Type-check passes

## References
- `projects/application/frontend/app/src/features/mastra-agents/pages/ConversationalAI.tsx` — React chat page
- `projects/application/frontend/app/src/features/mastra-agents/chat/message-list/` — message list components
- `projects/application/frontend/app/src/features/mastra-agents/chat/message-input/` — input component
- `projects/application/e2e/app/tests/chat/send-message.spec.ts` — E2E chat test selectors
