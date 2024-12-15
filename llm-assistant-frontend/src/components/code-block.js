import { LitElement, html, css } from "lit";
import Prism from "prismjs";
import "prismjs/themes/prism-tomorrow.css";
import "prismjs/components/prism-python";
import "prismjs/components/prism-javascript";
import "prismjs/components/prism-typescript";
import "prismjs/components/prism-bash";
import "prismjs/components/prism-json";
import "prismjs/components/prism-markdown";
import "prismjs/components/prism-yaml";
import "prismjs/components/prism-css";

class CodeBlock extends LitElement {
  static get properties() {
    return {
      language: {
        type: String,
      },
      code: {
        type: String,
        attribute: false,
      },
      theme: {
        type: String,
      },
    };
  }

  constructor() {
    super();
    this.language = "text";
    this.theme = "prism-tomorrow";
  }

  async updated() {
    try {
      const highlight = Prism.highlight(
        this.code || '',
        Prism.languages[this.language] || Prism.languages.text,
        this.language
      );
      this.shadowRoot.querySelector('#output').innerHTML = highlight;
    } catch(err) {
      console.error('Highlighting failed:', err);
      this.shadowRoot.querySelector('#output').textContent = this.code;
    }
  }

  static get styles() {
    return css`
      :host {
        display: block;
        margin: 8px 0;
      }
      
      pre {
        margin: 0;
        padding: 1em;
        overflow-x: auto;
        background: #2d2d2d;
        border-radius: 4px;
      }

      code {
        font-family: 'Fira Code', monospace;
        font-size: 0.9em;
        line-height: 1.5;
      }

      .header {
        background: #222;
        color: #fafafa;
        padding: 8px 16px;
        border-radius: 4px 4px 0 0;
        font-size: 0.9em;
      }
    `;
  }

  render() {
    return html`
      <div class="header">${this.language}</div>
      <pre class="language-${this.language}"><code id="output"></code></pre>
    `;
  }
}

customElements.define("code-block", CodeBlock);
