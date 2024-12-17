import { LitElement, html, css } from 'lit';

export class ContextPanel extends LitElement {
  static properties = {
    query: { type: String },
    isVisible: { type: Boolean },
    contexts: { type: Array }
  };

  constructor() {
    super();
    this.query = '';
    this.isVisible = false;
    this.contexts = [];
  }

  static styles = css`
    :host {
      position: fixed;
      right: 0;
      top: 0;
      height: 100vh;
      z-index: 50;
    }

    .panel-wrapper {
      height: 100%;
      position: relative;
    }

    .toggle-button {
      position: absolute;
      left: -40px;
      width: 40px;
      height: 120px;
      writing-mode: vertical-rl;
      text-orientation: mixed;
      transform: rotate(0deg);
      background-color: rgb(59, 130, 246);
      color: white;
      border: none;
      cursor: pointer;
      border-radius: 4px 0 0 4px;
      transition: background-color 0.2s;
    }

    .toggle-button:hover {
      background-color: rgb(37, 99, 235);
    }

    .toggle-button:focus {
      outline: none;
      ring: 2px;
      ring-color: rgb(59, 130, 246);
    }

    .panel-container {
      width: 320px;
      height: 100%;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      background-color: #2d2d2d;
      border-radius: 0 0 4px 4px;
      box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
      border-left: 1px solid #111;
    }

    .panel-container.visible {
      transform: translateX(0);
    }

    .title-text {
      text-align: center;
      padding: 10px;
      background-color: #222;
    }
    
    .text-context {
        padding: 10px;
    }
  `;

  togglePanel() {
    this.isVisible = !this.isVisible;
  }

  async fetchContext(query) {
    try {
      const response = await fetch('http://localhost:8001/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          query: query,
          num_results: 5,
          min_similarity: 0.1
        })
      });

      const data = await response.json();
      this.contexts = data.results.map(result => ({
        text: result.text,
        source: result.metadata.source,
        similarity: result.metadata.similarity,
        relevance: result.metadata.relevance
      }));
    } catch (error) {
      console.error('Error fetching context:', error);
    }
  }

  render() {
    return html`
      <div class="panel-wrapper">
        <div class="panel-container ${this.isVisible ? 'visible' : ''} bg-white shadow-lg">
          <button
            @click=${this.togglePanel}
            class="toggle-button"
          >
            Context ${this.isVisible ? '←' : '→'}
          </button>

          <div class="h-full flex flex-col">
            <div class="px-4 py-3 border-b border-gray-200 bg-gray-50">
              <h3 class="text-lg font-semibold text-gray-700 title-text">Related Context</h3>
            </div>

            <div class="flex-1 overflow-y-auto p-4 space-y-3">
              ${this.contexts.length === 0 
                ? html`<p class="text-gray-500 text-context italic">No context available</p>`
                : this.contexts.map(context => html`
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200 
                              hover:border-gray-300 transition-colors duration-200
                              hover:shadow-sm text-context">
                      <p class="text-gray-700 text-sm leading-relaxed mb-2">${context.text}</p>
                      <div class="flex items-center justify-between text-xs text-gray-500 border-t border-gray-200 pt-2 mt-2">
                        <span>Source: ${context.source}</span>
                        <span>Relevance: ${context.relevance.toLowerCase()}</span>
                        <span>Similarity: ${(context.similarity * 100).toFixed(1)}%</span>
                      </div>
                    </div>
                  `)
              }
            </div>
          </div>
        </div>
      </div>
    `;
  }
}

customElements.define('context-panel', ContextPanel); 