import { LitElement, html, css } from 'lit';
import { styles } from './styles.js';
import { marked } from 'marked';
import { unsafeHTML } from 'lit/directives/unsafe-html.js';

class LlmAssistantFrontend extends LitElement {
  static properties = {
    messages: { type: Array },
    inputText: { type: String },
    isLoading: { type: Boolean },
    waitingForFirstToken: { type: Boolean }
  };

  static styles = [styles];

  constructor() {
    super();
    this.messages = [];
    this.inputText = '';
    this.isLoading = false;
    this.waitingForFirstToken = false;
  }

  async sendMessage() {
    if (!this.inputText.trim()) return;

    const userMessage = {
      role: 'user',
      content: this.inputText.trim()
    };

    this.messages = [...this.messages, userMessage];
    this.inputText = '';
    this.isLoading = true;
    this.waitingForFirstToken = true;

    const assistantMessage = {
      role: 'assistant',
      content: ''
    };
    this.messages = [...this.messages, assistantMessage];

    this.updateComplete.then(() => {
      const container = this.shadowRoot.querySelector('.message-container');
      container.scrollTop = container.scrollHeight;
    });

    try {
      const response = await fetch('http://localhost:8080/chat/stream', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          messages: this.messages.slice(0, -1),
          temperature: 0.7,
          max_tokens: 2000
        })
      });

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(5));
              if (data.text) {
                this.waitingForFirstToken = false;
                assistantMessage.content += data.text;
                this.messages = [...this.messages.slice(0, -1), assistantMessage];
                
                this.updateComplete.then(() => {
                  const container = this.shadowRoot.querySelector('.message-container');
                  container.scrollTop = container.scrollHeight;
                });
              }
              if (data.error) {
                console.error('Error:', data.error);
              }
            } catch (e) {
              console.error('Failed to parse SSE data:', e);
            }
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
    } finally {
      this.isLoading = false;
      this.waitingForFirstToken = false;
    }
  }

  handleKeyPress(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      this.sendMessage();
    }
  }

  formatContent(message) {
    if (message.role === 'assistant') {
      return unsafeHTML(marked.parse(message.content));
    }
    return message.content;
  }

  render() {
    return html`
      <div class="flex flex-col h-full bg-gray-100">
        <!-- Centered title with flex -->
        <div class="border-b bg-white py-6 flex justify-center items-center">
          <h1 class="text-2xl font-semibold text-gray-800" style="margin-left: auto; margin-right: auto; width: 100%;">Personal AI Assistant</h1>
        </div>

        <!-- Messages Container -->
        <div class="message-container flex-1 p-4 space-y-4">
          ${this.messages.map((message, index) => html`
            <div class="flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}">
              <div class="${message.role === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-white text-gray-800'} 
                rounded-xl p-[10px] max-w-[80%] shadow-sm markdown-body">
                ${this.formatContent(message)}
                ${message.role === 'assistant' && 
                  index === this.messages.length - 1 && 
                  this.waitingForFirstToken ? html`
                  <div class="typing-indicator">
                    <div class="dot"></div>
                    <div class="dot" style="animation-delay: 0.2s"></div>
                    <div class="dot" style="animation-delay: 0.4s"></div>
                  </div>
                ` : ''}
              </div>
            </div>
          `)}
        </div>

        <!-- Input Area -->
        <div class="border-t bg-white p-4">
          <div class="flex space-x-4">
            <textarea
              class="flex-1 border rounded-lg p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="1"
              placeholder="Type your message..."
              .value=${this.inputText}
              @input=${e => this.inputText = e.target.value}
              @keypress=${this.handleKeyPress}
              ?disabled=${this.isLoading}
            ></textarea>
            <button
              class="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-400"
              @click=${this.sendMessage}
              ?disabled=${this.isLoading}
            >
              ${this.isLoading ? 'Sending...' : 'Send'}
            </button>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('llm-assistant-frontend', LlmAssistantFrontend);