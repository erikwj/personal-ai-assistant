import { LitElement, html, css } from 'lit';
import { styles } from './styles.js';
import { marked } from 'marked';
import './components/chat-window.js';

class LlmAssistantFrontend extends LitElement {
  static properties = {
    messages: { type: Array },
    inputText: { type: String },
    isLoading: { type: Boolean },
    waitingForFirstToken: { type: Boolean }
  };

  static styles = [
    styles
  ];

  constructor() {
    super();
    this.messages = [];
    this.inputText = '';
    this.isLoading = false;
    this.waitingForFirstToken = false;
  }

  handleInputChange(e) {
    this.inputText = e.detail;
  }

  async sendMessage(e) {
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

  render() {
    return html`
        <chat-window
          .messages=${this.messages}
          .inputText=${this.inputText}
          .isLoading=${this.isLoading}
          .waitingForFirstToken=${this.waitingForFirstToken}
          @input-change=${this.handleInputChange}
          @send-message=${this.sendMessage}
        ></chat-window>
    `;
  }
}

customElements.define('llm-assistant-frontend', LlmAssistantFrontend);