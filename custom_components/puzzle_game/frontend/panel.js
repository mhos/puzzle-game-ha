/**
 * Puzzle Game Panel for Home Assistant
 * Auto-registers in sidebar, no manual dashboard setup needed
 */

class PuzzleGamePanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._hass = null;
    this._lastMessage = null;
    this._feedbackTimeout = null;
    this._updateInterval = null;
  }

  set hass(hass) {
    this._hass = hass;
    this._updateDisplay();
  }

  connectedCallback() {
    this._render();
    // Update every 2 seconds
    this._updateInterval = setInterval(() => this._updateDisplay(), 2000);
  }

  disconnectedCallback() {
    if (this._updateInterval) {
      clearInterval(this._updateInterval);
    }
    if (this._feedbackTimeout) {
      clearTimeout(this._feedbackTimeout);
    }
  }

  _render() {
    this.shadowRoot.innerHTML = `
      <style>
        * {
          margin: 0;
          padding: 0;
          box-sizing: border-box;
        }

        :host {
          display: block;
          font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          color: white;
          padding: 10px;
        }

        .container {
          background: rgba(255, 255, 255, 0.1);
          backdrop-filter: blur(10px);
          border-radius: 20px;
          padding: 20px;
          width: 95%;
          max-width: 1000px;
          box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }

        .header {
          text-align: center;
          margin-bottom: 15px;
        }

        .header h1 {
          font-size: clamp(1.5em, 5vw, 3em);
          margin-bottom: 10px;
          text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .game-id {
          font-size: clamp(0.7em, 2vw, 0.9em);
          opacity: 0.7;
          font-family: monospace;
        }

        .stats {
          display: flex;
          justify-content: space-around;
          margin-bottom: 15px;
          flex-wrap: wrap;
          gap: 10px;
        }

        .stat {
          background: rgba(255, 255, 255, 0.2);
          padding: 10px 15px;
          border-radius: 15px;
          text-align: center;
          min-width: 80px;
          flex: 1;
        }

        .stat-label {
          font-size: clamp(0.7em, 2vw, 0.9em);
          opacity: 0.8;
          margin-bottom: 3px;
        }

        .stat-value {
          font-size: clamp(1.2em, 4vw, 2em);
          font-weight: bold;
        }

        .feedback-message {
          padding: 15px;
          border-radius: 15px;
          text-align: center;
          margin-bottom: 15px;
          font-size: clamp(1em, 3vw, 1.3em);
          font-weight: bold;
          display: none;
          animation: slideIn 0.3s ease-out;
        }

        .feedback-message.show {
          display: block;
        }

        .feedback-message.correct {
          background: rgba(76, 175, 80, 0.85);
          border: 2px solid rgba(76, 175, 80, 1);
          color: #ffffff;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }

        .feedback-message.wrong {
          background: rgba(244, 67, 54, 0.85);
          border: 2px solid rgba(244, 67, 54, 1);
          color: #ffffff;
          text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
        }

        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .solved-words {
          background: rgba(255, 215, 0, 0.2);
          border: 2px solid rgba(255, 215, 0, 0.5);
          padding: 15px;
          border-radius: 15px;
          text-align: center;
          margin-bottom: 15px;
          display: none;
        }

        .solved-words.show {
          display: block;
        }

        .solved-words-label {
          font-size: clamp(0.8em, 2vw, 1em);
          opacity: 0.9;
          margin-bottom: 10px;
          color: #ffd700;
          font-weight: bold;
        }

        .solved-words-list {
          font-size: clamp(1.1em, 3vw, 1.5em);
          font-weight: bold;
          letter-spacing: 1px;
          line-height: 1.5;
        }

        .word-display {
          background: rgba(255, 255, 255, 0.2);
          padding: 20px 5px;
          border-radius: 20px;
          text-align: center;
          margin-bottom: 15px;
          overflow: visible;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
        }

        .word-number {
          font-size: clamp(0.9em, 2.5vw, 1.2em);
          margin-bottom: 10px;
          opacity: 0.9;
        }

        .word-number.final-phase {
          color: #ffd700;
          font-weight: bold;
        }

        .word-blanks {
          font-size: clamp(1.1em, 2.5vw, 1.5em);
          letter-spacing: 0.15em;
          font-family: 'Courier New', monospace;
          font-weight: bold;
          margin: 10px 0;
          white-space: pre-wrap;
          word-wrap: break-word;
          padding: 5px 10px;
          width: 100%;
          max-width: 100%;
          display: block;
          overflow-wrap: break-word;
        }

        .clue {
          font-size: clamp(0.9em, 2.5vw, 1.3em);
          font-style: italic;
          margin-top: 10px;
          opacity: 0.9;
          line-height: 1.3;
        }

        .progress {
          display: flex;
          justify-content: center;
          gap: clamp(8px, 2vw, 15px);
          margin-top: 15px;
          flex-wrap: wrap;
        }

        .progress-dot {
          width: clamp(30px, 8vw, 40px);
          height: clamp(30px, 8vw, 40px);
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: clamp(1em, 3vw, 1.5em);
        }

        .progress-dot.correct {
          background: #4caf50;
        }

        .progress-dot.pending {
          background: rgba(255, 255, 255, 0.3);
          animation: pulse 2s infinite;
        }

        .progress-dot.final {
          background: #ffd700;
          font-size: clamp(0.8em, 2.5vw, 1.2em);
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.5; }
        }

        .footer {
          text-align: center;
          margin-top: 10px;
          opacity: 0.7;
          font-size: clamp(0.7em, 2vw, 0.9em);
        }

        .help-button {
          position: fixed;
          bottom: 10px;
          right: 10px;
          width: 40px;
          height: 40px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          border: 2px solid rgba(255, 255, 255, 0.5);
          color: white;
          font-size: 24px;
          font-weight: bold;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
          z-index: 1000;
          transition: all 0.3s ease;
        }

        .help-button:hover {
          background: rgba(255, 255, 255, 0.5);
          transform: scale(1.1);
        }

        .help-modal {
          display: none;
          position: fixed;
          top: 0;
          left: 0;
          width: 100%;
          height: 100%;
          background: rgba(0, 0, 0, 0.8);
          z-index: 2000;
          align-items: center;
          justify-content: center;
          padding: 20px;
        }

        .help-modal.show {
          display: flex;
        }

        .help-content {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          border-radius: 20px;
          padding: 25px;
          max-width: 600px;
          max-height: 80vh;
          overflow-y: auto;
          box-shadow: 0 20px 60px rgba(0,0,0,0.5);
        }

        .help-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 20px;
        }

        .help-title {
          font-size: 1.8em;
          font-weight: bold;
          color: white;
        }

        .help-close {
          width: 35px;
          height: 35px;
          border-radius: 50%;
          background: rgba(255, 255, 255, 0.3);
          border: 2px solid rgba(255, 255, 255, 0.5);
          color: white;
          font-size: 24px;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;
        }

        .help-section {
          background: rgba(255, 255, 255, 0.15);
          border-radius: 12px;
          padding: 15px;
          margin-bottom: 15px;
        }

        .help-section h3 {
          color: #ffd700;
          margin-bottom: 10px;
          font-size: 1.2em;
        }

        .help-command {
          background: rgba(0, 0, 0, 0.2);
          border-left: 3px solid #4caf50;
          padding: 8px 12px;
          margin-bottom: 8px;
          border-radius: 5px;
        }

        .help-command strong {
          color: #4caf50;
          display: block;
          margin-bottom: 3px;
        }

        .help-command span {
          color: rgba(255, 255, 255, 0.9);
          font-size: 0.9em;
        }

        /* Small screens */
        @media (max-width: 1024px) and (max-height: 600px) {
          :host {
            padding: 5px;
          }

          .container {
            padding: 10px;
            max-width: 100%;
            border-radius: 10px;
          }

          .header {
            margin-bottom: 8px;
          }

          .header h1 {
            font-size: 1.8em;
            margin-bottom: 5px;
          }

          .stats {
            margin-bottom: 8px;
            gap: 5px;
          }

          .stat {
            padding: 8px 12px;
            border-radius: 10px;
            min-width: 70px;
          }

          .word-display {
            padding: 12px 5px;
            margin-bottom: 8px;
            border-radius: 10px;
          }

          .word-blanks {
            font-size: 1.4em;
            letter-spacing: 0.1em;
            margin: 8px 0;
          }

          .progress {
            gap: 6px;
            margin-top: 8px;
          }

          .progress-dot {
            width: 28px;
            height: 28px;
            font-size: 0.9em;
          }

          .footer {
            margin-top: 5px;
            font-size: 0.6em;
          }
        }
      </style>

      <div class="help-button" id="helpBtn">?</div>

      <div class="help-modal" id="helpModal">
        <div class="help-content">
          <div class="help-header">
            <div class="help-title">Voice Commands</div>
            <div class="help-close" id="helpClose">×</div>
          </div>

          <div class="help-section">
            <h3>Starting the Game</h3>
            <div class="help-command">
              <strong>"Start puzzle game"</strong>
              <span>Begin a new puzzle with 5 words</span>
            </div>
            <div class="help-command">
              <strong>"Play bonus game"</strong>
              <span>Start a bonus round</span>
            </div>
          </div>

          <div class="help-section">
            <h3>Playing (No wake word needed!)</h3>
            <div class="help-command">
              <strong>Say the answer directly</strong>
              <span>Just say the word to submit</span>
            </div>
            <div class="help-command">
              <strong>"Spell"</strong>
              <span>Spell the word letter by letter</span>
            </div>
            <div class="help-command">
              <strong>"Reveal"</strong>
              <span>Show one random letter</span>
            </div>
            <div class="help-command">
              <strong>"Skip"</strong>
              <span>Move to next word</span>
            </div>
            <div class="help-command">
              <strong>"Repeat"</strong>
              <span>Hear the current clue again</span>
            </div>
          </div>

          <div class="help-section">
            <h3>Ending the Game</h3>
            <div class="help-command">
              <strong>"Pause" / "Give up"</strong>
              <span>Pause or end the game</span>
            </div>
          </div>

          <div class="help-section">
            <h3>How to Play</h3>
            <div class="help-command">
              <span>Solve 5 words, then guess the theme that connects them all. Each correct word earns 10 points. The final theme answer is worth 20 points!</span>
            </div>
          </div>
        </div>
      </div>

      <div class="container">
        <div class="header">
          <h1>🦉 Puzzle Game 🦉</h1>
          <div class="game-id" id="gameId">No active game</div>
        </div>

        <div class="stats">
          <div class="stat">
            <div class="stat-label">Score</div>
            <div class="stat-value" id="score">0</div>
          </div>
          <div class="stat">
            <div class="stat-label">Reveals</div>
            <div class="stat-value" id="reveals">0</div>
          </div>
        </div>

        <div class="feedback-message" id="feedbackMessage"></div>

        <div class="solved-words" id="solvedWordsSection">
          <div class="solved-words-label">🎯 Your Clue Words:</div>
          <div class="solved-words-list" id="solvedWords"></div>
        </div>

        <div class="word-display">
          <div class="word-number" id="wordNumberDisplay">Say "Start puzzle game"</div>
          <div class="word-blanks" id="blanks">_ _ _ _ _</div>
          <div class="clue" id="clue">Use your voice assistant to start playing!</div>
        </div>

        <div class="progress">
          <div class="progress-dot pending" id="word1">1</div>
          <div class="progress-dot" id="word2">2</div>
          <div class="progress-dot" id="word3">3</div>
          <div class="progress-dot" id="word4">4</div>
          <div class="progress-dot" id="word5">5</div>
          <div class="progress-dot" id="word6">🎯</div>
        </div>

        <div class="footer">
          Powered by AI
        </div>
      </div>
    `;

    // Set up help button events
    this.shadowRoot.getElementById("helpBtn").addEventListener("click", () => this._toggleHelp());
    this.shadowRoot.getElementById("helpClose").addEventListener("click", () => this._toggleHelp());
    this.shadowRoot.getElementById("helpModal").addEventListener("click", (e) => {
      if (e.target.id === "helpModal") this._toggleHelp();
    });
  }

  _toggleHelp() {
    const modal = this.shadowRoot.getElementById("helpModal");
    modal.classList.toggle("show");
  }

  _updateDisplay() {
    if (!this._hass) return;

    const sensor = this._hass.states["sensor.puzzle_game"];
    if (!sensor) return;

    const attrs = sensor.attributes || {};

    // Update game ID
    const gameIdEl = this.shadowRoot.getElementById("gameId");
    if (attrs.game_id) {
      gameIdEl.textContent = `Game: ${attrs.game_id.substring(0, 8)}...`;
    } else {
      gameIdEl.textContent = "No active game";
    }

    // Update stats
    this.shadowRoot.getElementById("score").textContent = attrs.score || 0;
    this.shadowRoot.getElementById("reveals").textContent = attrs.reveals || 0;

    // Show feedback message only when it changes
    if (attrs.last_message && attrs.last_message !== this._lastMessage) {
      this._showFeedback(attrs.last_message);
      this._lastMessage = attrs.last_message;
    }

    // Update word number display
    const wordNumEl = this.shadowRoot.getElementById("wordNumberDisplay");
    if (attrs.phase === 2) {
      wordNumEl.innerHTML = '<span style="color: #ffd700;">🎯 FINAL ANSWER</span>';
      wordNumEl.classList.add("final-phase");
    } else if (attrs.is_active) {
      wordNumEl.innerHTML = `Word ${attrs.word_number || 1} of 6`;
      wordNumEl.classList.remove("final-phase");
    } else if (attrs.theme_revealed) {
      wordNumEl.innerHTML = "Game Complete!";
      wordNumEl.classList.remove("final-phase");
    } else {
      wordNumEl.innerHTML = 'Say "Start puzzle game"';
      wordNumEl.classList.remove("final-phase");
    }

    // Update blanks and clue
    const blanksEl = this.shadowRoot.getElementById("blanks");
    const clueEl = this.shadowRoot.getElementById("clue");

    if (!attrs.is_active && attrs.theme_revealed) {
      blanksEl.textContent = attrs.theme_revealed;
      clueEl.textContent = `Score: ${attrs.score || 0}/70`;
    } else {
      blanksEl.textContent = attrs.blanks || "_ _ _ _ _";
      clueEl.textContent = attrs.clue || "Use your voice assistant to start playing!";
    }

    // Show solved words in phase 2
    const solvedSection = this.shadowRoot.getElementById("solvedWordsSection");
    const solvedWordsList = this.shadowRoot.getElementById("solvedWords");
    if (attrs.phase === 2 && attrs.solved_words && attrs.solved_words.length > 0) {
      solvedSection.classList.add("show");
      solvedWordsList.textContent = attrs.solved_words.join(" • ");
    } else {
      solvedSection.classList.remove("show");
    }

    // Update progress dots
    this._updateProgress(attrs.word_number || 1, attrs.phase || 1, attrs.solved_word_indices || []);
  }

  _showFeedback(message) {
    const feedbackEl = this.shadowRoot.getElementById("feedbackMessage");

    if (this._feedbackTimeout) {
      clearTimeout(this._feedbackTimeout);
    }

    const isCorrect = message.startsWith("Correct");

    feedbackEl.textContent = message;
    feedbackEl.className = "feedback-message show " + (isCorrect ? "correct" : "wrong");

    this._feedbackTimeout = setTimeout(() => {
      feedbackEl.classList.remove("show");
    }, 5000);
  }

  _updateProgress(currentWord, phase, solvedIndices) {
    if (!solvedIndices || !Array.isArray(solvedIndices)) {
      solvedIndices = [];
    }

    for (let i = 1; i <= 6; i++) {
      const dot = this.shadowRoot.getElementById(`word${i}`);
      if (!dot) continue;

      const wordIndex = i - 1;

      if (i === 6) {
        if (phase === 2) {
          dot.className = "progress-dot final pending";
          dot.textContent = "🎯";
        } else {
          dot.className = "progress-dot";
          dot.textContent = "🎯";
        }
      } else {
        const isSolved = solvedIndices.includes(wordIndex);

        if (isSolved) {
          dot.className = "progress-dot correct";
          dot.textContent = "✓";
        } else if (wordIndex === currentWord - 1 && phase === 1) {
          dot.className = "progress-dot pending";
          dot.textContent = i;
        } else {
          dot.className = "progress-dot";
          dot.textContent = i;
        }
      }
    }
  }
}

customElements.define("puzzle-game-panel", PuzzleGamePanel);
