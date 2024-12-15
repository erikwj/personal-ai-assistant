import { LitElement, html, css, unsafeCSS } from "lit";
import Prism from "prismjs";
import prismStyle from "../../node_modules/prismjs/themes/prism-tomorrow.css?inline";
import "../../node_modules/prismjs/components/prism-python";
import "../../node_modules/prismjs/components/prism-javascript";
import "../../node_modules/prismjs/components/prism-typescript";
import "../../node_modules/prismjs/components/prism-bash";
import "../../node_modules/prismjs/components/prism-json";
import "../../node_modules/prismjs/components/prism-markdown";
import "../../node_modules/prismjs/components/prism-yaml";
import "../../node_modules/prismjs/components/prism-css";
import "../../node_modules/prismjs/components/prism-go";
import "../../node_modules/prismjs/components/prism-java";

class CodeBlock extends LitElement {
  static get properties() {
    return {
      language: { type: String },
      code: { type: String, attribute: false },
      theme: { type: String },
    };
  }

  constructor() {
    super();
    this.language = "text";
    this.theme = "prism-tomorrow";
  }

  async updated() {
    try {
      const codeElement = this.shadowRoot.querySelector('code');
      if (!codeElement) return;

      // Add Prism's classes
      codeElement.className = `language-${this.language}`;
      
      // Apply highlighting
      const highlighted = Prism.highlight(
        this.code || '',
        Prism.languages[this.language] || Prism.languages.text,
        this.language
      );
      
      codeElement.innerHTML = highlighted;
    } catch(err) {
      console.error('Highlighting failed:', err);
      const codeElement = this.shadowRoot.querySelector('code');
      if (codeElement) {
        codeElement.textContent = this.code;
      }
    }
  }

  static get styles() {
    return [
      unsafeCSS(prismStyle),
      css`
        :host {
          display: block;
          margin: 8px 0;
        }
        
        pre {
          margin: 0;
          padding: 1em;
          overflow-x: auto;
          background: #222;
          border-radius: 0 0 4px 4px;
        }

        .header {
          background: #1a1a1a;
          color: #fdfdfd;
          padding: 8px 16px;
          border-radius: 4px 4px 0 0;
          font-size: 0.9em;
        }

        code {
          font-family: 'Fira Code', monospace;
          font-size: 14px;
        }

        /* Token colors */
        .token.comment { color: #6a9955; }
        .token.keyword { color: #569cd6; }
        .token.string { color: #ce9178; }
        .token.number { color: #b5cea8; }
        .token.operator { color: #d4d4d4; }
        .token.class-name { color: #4ec9b0; }
        .token.function { color: #dcdcaa; }
        .token.punctuation { color: #d4d4d4; }
      `
    ];
  }

  render() {
    return html`
      <div class="header">${this.language}</div>
      <pre><code></code></pre>
    `;
  }
}

customElements.define("code-block", CodeBlock);
