# AI Assisted Chef Setup and Engineering Notes

The AI assisted Chef lets users ring a bell in the sidebar to get up to three recipe ideas based on what is currently in their pantry, then ask follow-up questions in a sidebar chat.

**You don't need an API key to work on this project** as the project has the flexibility of fallback messages instead of crashing the web application, and all automated tests use mocks instead of testing the network or use tokens. In this way, we don't have to waste AI tokens that can otherwise be used for more complex behavior.

## ENGINEERING DECISIONS

- **Fallback messages over hard failures:** Missing keys, empty model output, network issues, or SDK errors in `core\ai_chef.py` return friendly/in-character replies (`FALLBACK_MESSAGE_1` / `FALLBACK_MESSAGE_2`) rather than throwing an unhandled error in `core/views.py`
- **Safe pantry filtering and bounded chat history:** `pantry_item_lookup()` filters out `"Expired"` items so expired food isn't pitched as safe to use, and `build_content()` slices `history[-6:]` so follow-up prompts stay focused and within context limits
- **Three stage sidebar flow:** The UI moves through `#chef-bell-stage` → `#chef-loading` (`"Summoning the Chef..."`) → `#chef-chat-room` in `home.html` and `core/static/js/ai_chef.js`, backed by a `[hidden]` CSS rule so only one stage shows at a time
- **10 second Client Timeout:** `ai_chef.js` uses an `AbortController` with a `10000ms` timeout so a slow or unreachable `/ai-chef/` request still transitions into the chatroom with a fallback message rather than leaving the user stuck on the spinner
- **Key and model configuration:** `DEFAULT_CHEF_MODEL` (`gemini-3.5-flash-lite`), `API_KEY_ENV_VAR` (`GEMINI_API_KEY`), and `CHEF_API_KEY` sit near the top of `core/ai_chef.py` so anyone reading the file can find them fast without hardcoding secrets in Git


## Get a Key and Install Dependencies

1. Install the Gemini SDK listed in the `requirements.txt` (`google-genai`) inside of your virtual environment.
2. Create a Gemini API key and keep it in your environment (Do not paste real keys into `CHEF_API_KEY` or commit `.env` to Git)

## API key setup

Create a `.env` file inside the `project/` directory (alongside `manage.py`)

```env
GEMINI_API_KEY=your_gemini_key
AI_CHEF_MODEL=gemini-3.5-flash-lite
```

## How to use it
1. Start the server, log in, open the sidebar menu, and click **Ai assisted Chef** (`#panel-ai`)
2. Click **Ring for Chef** (`#chef-bell-btn`) to phase out the bell, show the loading indicator, and load recipe suggestions into `#chef-chat-room`
3. Ask follow-up questions in `#chef-message-input` and submit `#chef-chat-form`
4. Run `pytest` from `project/` anytime to verify backend and endpoint behavior without spending API quota