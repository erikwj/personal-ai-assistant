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

    .panel-container {
      width: 320px;
      height: 100vh;
      transform: translateX(100%);
      transition: transform 0.3s ease;
      background-color: #2d2d2d;
      border-radius: 0 0 4px 4px;
      box-shadow: 0 0 10px 0 rgba(0, 0, 0, 0.1);
      border-left: 1px solid #111;
      display: flex;
      flex-direction: column;
    }

    .panel-container.visible {
      transform: translateX(0);
    }

    .panel-header {
      flex: 0 0 auto;
      border-bottom: 1px solid #e5e7eb;
      background-color: #222;
    }

    .panel-content {
      flex: 1 1 auto;
      overflow-y: auto;
      padding: 1rem;
    }

    .context-items {
      display: flex;
      flex-direction: column;
      gap: 0.75rem;
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

    .title-text {
      text-align: center;
      padding: 10px;
      background-color: #222;
    }
    
    .text-context {
        padding: 10px;
    }

    .metadata-container {
      display: flex;
      flex-wrap: wrap;
      gap: 0.75rem;
      padding-top: 0.75rem;
      margin-top: 0.75rem;
      border-top: 1px solid #e5e7eb;
      font-size: 0.75rem;
      color: #6b7280;
    }

    .metadata-item {
      display: flex;
      align-items: center;
      gap: 0.25rem;
      min-width: fit-content;
    }

    .source-item {
      flex: 1 1 100%;
    }

    .metrics-container {
      display: flex;
      gap: 0.75rem;
      justify-content: space-between;
      width: 100%;
    }

    .metadata-label {
      font-weight: 500;
      color: #4b5563;
    }

    .metadata-value {
      color: #6b7280;
    }

    .relevance-badge {
      padding: 0.25rem 0.5rem;
      border-radius: 9999px;
      font-weight: 500;
      text-transform: capitalize;
    }

    .relevance-high {
      background-color: #dcfce7;
      color: #166534;
    }

    .relevance-medium {
      background-color: #fef9c3;
      color: #854d0e;
    }

    .relevance-low {
      background-color: #fee2e2;
      color: #991b1b;
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

          <div class="panel-header">
            <h3 class="text-lg font-semibold text-gray-700 title-text">Related Context</h3>
          </div>

          <div class="panel-content">
            <div class="context-items">
              ${this.contexts.length === 0 
                ? html`<p class="text-gray-500 text-context italic">No context available</p>`
                : this.contexts.map(context => html`
                    <div class="bg-gray-50 rounded-lg p-3 border border-gray-200 
                              hover:border-gray-300 transition-colors duration-200
                              hover:shadow-sm text-context">
                      <p class="text-gray-700 text-sm leading-relaxed mb-2">${context.text}</p>
                      <div class="metadata-container">
                        <div class="metadata-item source-item">
                          <span class="metadata-label">Source:</span>
                          <span class="metadata-value">${context.source}</span>
                        </div>
                        <div class="metrics-container">
                          <div class="metadata-item">
                            <span class="relevance-badge relevance-${context.relevance.toLowerCase()}">
                              ${context.relevance.toLowerCase()}
                            </span>
                          </div>
                          <div class="metadata-item">
                            <span class="metadata-label">Similarity:</span>
                            <span class="metadata-value">${context.similarity.toFixed(3)}</span>
                          </div>
                        </div>
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