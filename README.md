### 🚀 GameLab CS 2025 - 2026 Academic Project
WordPuyo

Developed by **Zeshan MA** & **Luke OGURO**, **7x7 Word Battle** is a premium, matrix-based word puzzle game written in Python using Pygame. Players strategically drop random letters onto a $7 \times 7$ grid to form words vertically, horizontally, or diagonally. Valid words vanish, triggering matrix gravity and awarding score multipliers!

---

## ✨ Features

* **Dual Operational Modes**:
  * ⚔️ **Arcade Mode**: A high-stakes, 300-second blitz session. Every word found adds $+3$ seconds back to your timeline. High scores are instantly streamed to a global Firebase Cloud Leaderboard.
  * 📚 **Practice Mode**: An untimed, infinite environment designed to test matrix endurance and explore complex letter patterns without cloud ranking interference.
* **Lexical Validation Suite**: Powered by `nltk`, validating words dynamically in both forward and backward orientations.
* **Premium Theme**: Styled with a dark, high-contrast visual interface, anti-aliased geometry layouts, and responsive particle animation engines.
* **Crash-Resistant Font Architecture**: Features a defensive fallback rendering engine designed to automatically bypass Windows Win32 font registry corruption bugs.

---

## 🛠️ Prerequisites & Installation

Make sure you have Python installed. Install the necessary dependencies before launching the program:

```bash
pip install pygame requests nltk
