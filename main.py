import json
import os
import random
import time
import re

# ANSI color codes
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
RED = "\033[91m"
YELLOW = "\033[33m"
RESET = "\033[0m"
CLEAR = "\033[2J\033[H"

BASE_DIR = os.path.dirname(__file__)
PROBLEMS_FILE = os.path.join(BASE_DIR, "problems.json")

DIGIT_TO_CATEGORY = {
    "1": "optimization",
    "2": "derivative",
    "3": "integral",
    "4": "continuity",
    "5": "limit",
    "6": "chain_rule",
    "7": "definite_integral",
}

ATTACKS = {
    "optimization": {"name": "Optimization", "damage": 30, "cost": 60, "once_per_round": True, "fail_self_mult": 0.75},
    "derivative": {"name": "Derivative", "damage": 8, "cost": 20, "once_per_round": False, "fail_self_mult": 0.5},
    "integral": {"name": "Integral", "damage": 5, "cost": 25, "once_per_round": False, "fail_self_mult": 0.2},
    "continuity": {"name": "Continuity", "damage": 0, "cost": 15, "once_per_round": True, "fail_self_mult": 1.0},
    "limit": {"name": "Limit", "damage": 0, "cost": 10, "once_per_round": False, "fail_self_mult": 0.0},
    "chain_rule": {"name": "Chain Rule", "damage": 12, "cost": 30, "once_per_round": False, "fail_self_mult": 0.5},
    "definite_integral": {"name": "Definite Integral", "damage": 40, "cost": 80, "once_per_round": True, "fail_self_mult": 1.0, "two_turn": True},
}


def load_problems(path=PROBLEMS_FILE):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    out = {}
    qroot = data.get("questions", {})
    for cat in DIGIT_TO_CATEGORY.values():
        catobj = qroot.get(cat, {}).get("questions", {})
        pairs = []
        for qid, qdata in catobj.items():
            q = qdata.get("question")
            a = qdata.get("answer")
            if q and a:
                pairs.append((q, a))
        out[cat] = pairs
    return out


def fallback_question(category):
    # Simple fallback problems so the primer runs even with empty JSON
    if category == "limit":
        return ("Compute limit: lim_{x->0} (sin(x)/x). Answer as a number.", 1)
    if category == "derivative":
        return ("Derivative: d/dx (x**2) at x=3.", 6)
    if category == "integral":
        return ("Integral: int_0^1 2*x dx. Answer as a number.", 1)
    if category == "optimization":
        return ("Find min of f(x)= (x-2)**2. What is the minimum value?", 0)
    if category == "continuity":
        return ("Is f(x)=1/x continuous at x=0? (yes/no)", "no")
    if category == "chain_rule":
        return ("Compute derivative of f(x)=(x**2 + 1)**2 at x=1.", 4)
    if category == "definite_integral":
        return ("Compute int_0^2 x dx.", 2)
    return ("What is 1+1?", 2)


def get_problem(problems, category):
    pool = problems.get(category, [])
    if pool:
        q, a = random.choice(pool)
        return q, a
    return fallback_question(category)


def match_answer(ans, a):
    """Return True if answer string `ans` matches expected `a`.

    Supports numeric expected values, plain strings, and regex answers prefixed
    with `re:` or slash-delimited `/pattern/flags`.
    """
    ans_str = str(ans).strip()
    # numeric expected answer (int/float)
    try:
        if isinstance(a, (int, float)):
            return abs(float(ans_str) - float(a)) < 1e-6
        if isinstance(a, str):
            a_str = a.strip()
            # if the expected answer string looks numeric, compare numerically
            try:
                a_num = float(a_str)
                return abs(float(ans_str) - a_num) < 1e-6
            except Exception:
                # regex support: prefix with "re:" or /pattern/flags
                if a_str.startswith("re:"):
                    pattern = a_str[3:]
                    return bool(re.fullmatch(pattern, ans_str, re.IGNORECASE))
                elif len(a_str) >= 2 and a_str[0] == "/" and a_str.rfind("/") > 0:
                    last = a_str.rfind("/")
                    pattern = a_str[1:last]
                    flags = a_str[last+1:]
                    re_flags = 0
                    if "i" in flags:
                        re_flags |= re.IGNORECASE
                    return bool(re.fullmatch(pattern, ans_str, re_flags))
                else:
                    return ans_str.lower() == a_str.lower()
    except Exception:
        return ans_str.lower() == str(a).strip().lower()


def get_attack_damage(attack_key, quick=False):
    """Return the (possibly boosted) damage for an attack key.

    Uses the same 1.25x multiplier applied when `quick` is True.
    """
    atk = ATTACKS.get(attack_key, {})
    base = int(atk.get("damage", 0))
    if quick:
        return int(base * 1.25)
    return base



def is_valid_sequence(seq):
    # Backwards-compatible boolean check using the regex parser
    return parse_sequence(seq) is not None


def parse_sequence(raw):
    """Parse a player's free-form input and extract the first three digits 1-7.

    Accepts inputs like '1 2 3', '1-2-3', 'digits:123', or 'abc1,2,3xyz'.
    Returns a compact 3-character string like '123' or None if invalid.
    """
    if not isinstance(raw, str):
        return None
    # Find all digits in the 1-7 range
    digits = re.findall(r"[1-7]", raw)
    if len(digits) < 3:
        return None
    return "".join(digits[:3])


def ask_question(player_name, category, problems):
    q, a = get_problem(problems, category)
    print(f"{player_name}, solve this ({category}):")
    print(q)
    start = time.time()
    ans = input("Answer: ").strip()
    elapsed = time.time() - start
    # interpret expected answer using helper
    correct = match_answer(ans, a)

    # Bonus window: answers given between 90 and 120 seconds (inclusive)
    quick = 90 <= elapsed <= 120
    return correct, quick


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def show_intro():
    """Display the intro screen"""
    print(CLEAR, end="")
    print("-" * 60)
    print(f"{BOLD}{CYAN}------- BasCalc: Mathematical Calculus Battle -------{RESET}")
    print("-" * 60)
    print(f"{BOLD}{YELLOW}------- A Two-Player Combat Game -------{RESET}")
    print("-" * 60)
    print("")
    print(f"{BOLD}The Rules:{RESET}")
    print("  • This is a two-player game")
    print("  • Enter your name and your opponent's name")
    print(f"  • Each round, both players enter a {BOLD}3-digit attack sequence{RESET}")
    print(f"    Digits 1-7 correspond to math attacks:")
    print(f"      {GREEN}1 = Optimization{RESET}   {GREEN}2 = Derivative{RESET}     {GREEN}3 = Integral{RESET}")
    print(f"      {GREEN}4 = Continuity{RESET}     {GREEN}5 = Limit{RESET}          {GREEN}6 = Chain Rule{RESET}")
    print(f"      {GREEN}7 = Definite Integral{RESET}")
    print("")
    print(f"  • {BOLD}Answer math questions{RESET} correctly to deal damage to your opponent")
    print(f"  • Answer {BOLD}within 90-120 seconds{RESET} for bonus damage (+25%)")
    print(f"  • Manage your {YELLOW}Brain Power{RESET} resource to execute attacks")
    print(f"  • Some attacks can only be used once per round")
    print(f"  • First player to reduce opponent HP to 0 wins!")
    print("")
    print("-" * 60)
    print(f"{BOLD}{CYAN}May the Best Mathematician Win!{RESET}")
    print("-" * 60)
    print("")



def main(prev_p1=None, prev_p2=None):
    show_intro()
    problems = load_problems()

    # reuse previous names when provided (on replay)
    if prev_p1 is not None:
        p1 = prev_p1
    else:
        p1 = input(f"{BOLD}Player 1 name: {RESET}").strip() or "Player1"

    if prev_p2 is not None:
        p2 = prev_p2
    else:
        p2 = input(f"{BOLD}Player 2 name: {RESET}").strip() or "Player2"

    state = {
        p1: {"hp": 100, "brain": 150, "pending": 0, "used_once": set()},
        p2: {"hp": 100, "brain": 150, "pending": 0, "used_once": set()},
    }

    print(CLEAR, end="")
    print(f"{BOLD}{CYAN}=== Game Start ==={RESET}")
    print(f"{BOLD}{CYAN}{p1}{RESET} vs {BOLD}{CYAN}{p2}{RESET}")
    time.sleep(2)

    round_no = 1
    while state[p1]["hp"] > 0 and state[p2]["hp"] > 0:
        print(CLEAR, end="")
        print(f"{BOLD}{CYAN}=== Round {round_no} ==={RESET}")
        print(f"{YELLOW}{p1}:{RESET} {GREEN}{state[p1]['hp']} HP{RESET}, {YELLOW}{state[p1]['brain']} brain{RESET} || {YELLOW}{p2}:{RESET} {GREEN}{state[p2]['hp']} HP{RESET}, {YELLOW}{state[p2]['brain']} brain{RESET}")
        print("")
        # short help note each round about accepted answer formats
        print(f"{CYAN}Note:{RESET} Answers accept implicit multiplication (e.g. `2x` or `2*x`), Unicode mul `·` or `×`, superscripts (² ³ ⁴), and optional `= RHS`.")
        print("")

        seq1_raw = input(f"{BOLD}{p1}, enter 3-digit attack sequence (digits 1-7): {RESET}")
        seq1 = parse_sequence(seq1_raw)
        while not seq1:
            seq1 = parse_sequence(input(f"{RED}Invalid sequence. Try again: {RESET}"))

        seq2_raw = input(f"{BOLD}{p2}, enter 3-digit attack sequence (digits 1-7): {RESET}")
        seq2 = parse_sequence(seq2_raw)
        while not seq2:
            seq2 = parse_sequence(input(f"{RED}Invalid sequence. Try again: {RESET}"))

        # per-round flags
        state[p1]["used_once"] = set()
        state[p2]["used_once"] = set()

        for i in range(3):
            a1 = DIGIT_TO_CATEGORY[seq1[i]]
            a2 = DIGIT_TO_CATEGORY[seq2[i]]

            # apply pending deferred damage from two-turn attacks
            for pl, other in ((p1, p2), (p2, p1)):
                pending = state[pl].get("pending", 0)
                if pending:
                    print(f"{RED}{pl} releases deferred damage: {pending} to self{RESET}")
                    state[pl]["hp"] -= pending
                    state[pl]["pending"] = 0

            # special simple interaction: derivative vs integral
            derivative_blocked = (a1 == "derivative" and a2 == "integral") or (a2 == "derivative" and a1 == "integral")

            # resolve player1 action
            atk1 = ATTACKS[a1]
            if atk1.get("once_per_round") and a1 in state[p1]["used_once"]:
                print(f"{RED}{p1} tried to reuse {atk1['name']} this round — skipped{RESET}")
            elif state[p1]["brain"] < atk1["cost"]:
                print(f"{RED}{p1} lacks brainpower for {atk1['name']} — skipped{RESET}")
            else:
                state[p1]["brain"] -= atk1["cost"]
                correct, quick = ask_question(p1, a1, problems)
                if correct and not (a1 == "derivative" and derivative_blocked and a2 == "integral"):
                    damage = get_attack_damage(a1, quick)
                    print(f"{GREEN}{p1} succeeded: {a1} deals {damage} to {p2}{RESET}")
                    state[p2]["hp"] -= damage
                    if atk1.get("two_turn"):
                        # store fraction to self for next turn as demonstration
                        state[p1]["pending"] += int(damage * 0.25)
                else:
                    selfd = int(atk1["damage"] * atk1.get("fail_self_mult", 0.5))
                    print(f"{RED}{p1} failed {a1}; takes {selfd} self-damage{RESET}")
                    state[p1]["hp"] -= selfd
                if atk1.get("once_per_round"):
                    state[p1]["used_once"].add(a1)

            # resolve player2 action (mirror)
            atk2 = ATTACKS[a2]
            if atk2.get("once_per_round") and a2 in state[p2]["used_once"]:
                print(f"{RED}{p2} tried to reuse {atk2['name']} this round — skipped{RESET}")
            elif state[p2]["brain"] < atk2["cost"]:
                print(f"{RED}{p2} lacks brainpower for {atk2['name']} — skipped{RESET}")
            else:
                state[p2]["brain"] -= atk2["cost"]
                correct, quick = ask_question(p2, a2, problems)
                if correct and not (a2 == "derivative" and derivative_blocked and a1 == "integral"):
                    damage = get_attack_damage(a2, quick)
                    print(f"{GREEN}{p2} succeeded: {a2} deals {damage} to {p1}{RESET}")
                    state[p1]["hp"] -= damage
                    if atk2.get("two_turn"):
                        state[p2]["pending"] += int(damage * 0.25)
                else:
                    selfd = int(atk2["damage"] * atk2.get("fail_self_mult", 0.5))
                    print(f"{RED}{p2} failed {a2}; takes {selfd} self-damage{RESET}")
                    state[p2]["hp"] -= selfd
                if atk2.get("once_per_round"):
                    state[p2]["used_once"].add(a2)

            # clamp values and report
            state[p1]["hp"] = clamp(state[p1]["hp"]) 
            state[p2]["hp"] = clamp(state[p2]["hp"]) 
            state[p1]["brain"] = clamp(state[p1]["brain"], 0, 150)
            state[p2]["brain"] = clamp(state[p2]["brain"], 0, 150)

            print(f"After sequence {i+1}: {YELLOW}{p1}:{RESET} {GREEN}{state[p1]['hp']} HP{RESET}, {YELLOW}{state[p1]['brain']} brain{RESET} || {YELLOW}{p2}:{RESET} {GREEN}{state[p2]['hp']} HP{RESET}, {YELLOW}{state[p2]['brain']} brain{RESET}")
            print("")

            # check end
            if state[p1]["hp"] <= 0 or state[p2]["hp"] <= 0:
                break

        round_no += 1
        time.sleep(1)

    # outcome
    print(CLEAR, end="")
    print(f"{BOLD}{RED}=== Game Over ==={RESET}")
    print(f"Final: {YELLOW}{p1}:{RESET} {GREEN}{state[p1]['hp']} HP{RESET} || {YELLOW}{p2}:{RESET} {GREEN}{state[p2]['hp']} HP{RESET}")
    
    winner = p1 if state[p1]["hp"] > 0 else (p2 if state[p2]["hp"] > 0 else "Nobody")
    if winner != "Nobody":
        print(f"\n{BOLD}{GREEN}🏆 {winner} wins! 🏆{RESET}")
    else:
        print(f"\n{BOLD}{YELLOW}It's a draw!{RESET}")

    print("")

    return p1, p2


if __name__ == "__main__":
    prev_p1 = None
    prev_p2 = None
    while True:
        prev_p1, prev_p2 = main(prev_p1, prev_p2)
        # prompt to play again or exit
        play_again = input("Would you like to play again or quit? (R=Replay / E=Exit): ").strip().lower()
        while play_again not in ("r", "e"):
            print("Invalid input, enter 'R' to replay or 'E' to exit.")
            play_again = input("Would you like to play again or quit? (R=Replay / E=Exit): ").strip().lower()
        if play_again == "r":
            print("Rebooting the game...\n")
            time.sleep(1)
            continue
        else:
            print("Thanks for playing. Exiting now.")
            break
