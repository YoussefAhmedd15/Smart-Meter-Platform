import sys
from pathlib import Path

# Ensure project root and ai_training are in python path
SCRIPT_DIR = Path(__file__).resolve().parent
AI_TRAINING_DIR = SCRIPT_DIR.parent
PROJECT_ROOT = AI_TRAINING_DIR.parent

for p in [str(PROJECT_ROOT), str(AI_TRAINING_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from ai_training.agent.agent import L1Agent
from ai_training.agent.conversation import ConversationManager


def print_banner():
    print("=" * 70)
    print("ISKRA SMART METER — AI L1 SUPPORT AGENT")
    print("=" * 70)
    print("Intelligent, grounded technical support for ISKRA smart meters.")
    print("Commands:")
    print("  reset   -> Start a fresh case")
    print("  state   -> View current structured case memory snapshot")
    print("  debug   -> Toggle diagnostic mode (intent, facts, routing)")
    print("  exit    -> Exit the agent")
    print("=" * 70 + "\n")


def main():
    print_banner()

    manager = ConversationManager()
    show_debug = False

    while True:
        try:
            print("-" * 70)
            user_input = input("Customer: ").strip()
            print()

            if not user_input:
                continue

            cmd = user_input.lower()
            if cmd in ["exit", "quit", "q"]:
                print("Agent: Thank you for contacting ISKRA Technical Support. Goodbye!")
                break

            if cmd in ["reset", "new"]:
                manager.start_new_case()
                print("Agent: A new case has been opened. How can I assist you with your meter today?\n")
                continue

            if cmd == "debug":
                show_debug = not show_debug
                status = "ENABLED" if show_debug else "DISABLED"
                print(f"[DEBUG MODE {status}]\n")
                continue

            if cmd == "state":
                state = manager.get_case_state()
                print("\n[DIAGNOSTIC CASE STATE]")
                for k, v in state.items():
                    if v:
                        print(f"  {k:22}: {v}")
                print()
                continue

            response = manager.handle_message(user_input)
            print(f"Agent: {response.text}\n")

            if show_debug:
                state = manager.get_case_state()
                print("[DEBUG INFO]")
                print(f"  Domain   : {state.get('question_domain')}")
                print(f"  Intent   : {state.get('intent')}")
                print(f"  Action   : {response.action.value if hasattr(response.action, 'value') else response.action}")
                print(f"  Category : {state.get('issue_category')}")
                print(f"  Routing  : {state.get('routing')}")
                print(f"  Status   : {state.get('l1_status')}")
                print(f"  Facts    : {state.get('known_facts')}")
                print(f"  Evidence : {len(state.get('evidence', []))} items")
                for idx, ev in enumerate(state.get("evidence", [])[:2], 1):
                    ml = ev.get("matched_line") or ev.get("text", "")[:80]
                    print(f"    [{idx}] ({ev.get('evidence_type')}): {ml}")
                print()

        except (KeyboardInterrupt, EOFError):
            print("\nAgent: Session closed. Goodbye!")
            break
        except Exception as e:
            print(f"\n[ERROR]: An unexpected issue occurred: {e}\n")


if __name__ == "__main__":
    main()
