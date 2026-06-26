import json
import os
import random
import time

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


def is_valid_sequence(seq):
    return isinstance(seq, str) and len(seq) == 3 and all(c in DIGIT_TO_CATEGORY for c in seq)


def ask_question(player_name, category, problems):
    q, a = get_problem(problems, category)
    print(f"{player_name}, solve this ({category}):")
    print(q)
    start = time.time()
    ans = input("Answer: ").strip()
    elapsed = time.time() - start

    # interpret numeric expected answers
    correct = False
    try:
        # try numeric compare
        if isinstance(a, (int, float)):
            correct = abs(float(ans) - float(a)) < 1e-6
        else:
            correct = str(ans).strip().lower() == str(a).strip().lower()
    except Exception:
        correct = str(ans).strip().lower() == str(a).strip().lower()

    quick = elapsed <= 30
    return correct, quick


def clamp(v, lo=0, hi=100):
    return max(lo, min(hi, v))


def main():
    problems = load_problems()

    print("BasCalc primer — simple playable loop (prototype)")
    p1 = input("Player 1 name: ").strip() or "Player1"
    p2 = input("Player 2 name: ").strip() or "Player2"

    state = {
        p1: {"hp": 100, "brain": 150, "pending": 0, "used_once": set()},
        p2: {"hp": 100, "brain": 150, "pending": 0, "used_once": set()},
    }

    round_no = 1
    while state[p1]["hp"] > 0 and state[p2]["hp"] > 0:
        print(f"\n=== Round {round_no} ===")
        print(f"{p1}: {state[p1]['hp']} HP, {state[p1]['brain']} brain || {p2}: {state[p2]['hp']} HP, {state[p2]['brain']} brain")

        seq1 = input(f"{p1}, enter 3-digit attack sequence (digits 1-7): ")
        while not is_valid_sequence(seq1):
            seq1 = input("Invalid sequence. Try again: ")

        seq2 = input(f"{p2}, enter 3-digit attack sequence (digits 1-7): ")
        while not is_valid_sequence(seq2):
            seq2 = input("Invalid sequence. Try again: ")

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
                    print(f"{pl} releases deferred damage: {pending} to self")
                    state[pl]["hp"] -= pending
                    state[pl]["pending"] = 0

            # special simple interaction: derivative vs integral
            derivative_blocked = (a1 == "derivative" and a2 == "integral") or (a2 == "derivative" and a1 == "integral")

            # resolve player1 action
            atk1 = ATTACKS[a1]
            if atk1.get("once_per_round") and a1 in state[p1]["used_once"]:
                print(f"{p1} tried to reuse {atk1['name']} this round — skipped")
            elif state[p1]["brain"] < atk1["cost"]:
                print(f"{p1} lacks brainpower for {atk1['name']} — skipped")
            else:
                state[p1]["brain"] -= atk1["cost"]
                correct, quick = ask_question(p1, a1, problems)
                if correct and not (a1 == "derivative" and derivative_blocked and a2 == "integral"):
                    damage = atk1["damage"]
                    if quick:
                        damage = int(damage * 1.25)
                    print(f"{p1} succeeded: {a1} deals {damage} to {p2}")
                    state[p2]["hp"] -= damage
                    if atk1.get("two_turn"):
                        # store fraction to self for next turn as demonstration
                        state[p1]["pending"] += int(damage * 0.25)
                else:
                    selfd = int(atk1["damage"] * atk1.get("fail_self_mult", 0.5))
                    print(f"{p1} failed {a1}; takes {selfd} self-damage")
                    state[p1]["hp"] -= selfd
                if atk1.get("once_per_round"):
                    state[p1]["used_once"].add(a1)

            # resolve player2 action (mirror)
            atk2 = ATTACKS[a2]
            if atk2.get("once_per_round") and a2 in state[p2]["used_once"]:
                print(f"{p2} tried to reuse {atk2['name']} this round — skipped")
            elif state[p2]["brain"] < atk2["cost"]:
                print(f"{p2} lacks brainpower for {atk2['name']} — skipped")
            else:
                state[p2]["brain"] -= atk2["cost"]
                correct, quick = ask_question(p2, a2, problems)
                if correct and not (a2 == "derivative" and derivative_blocked and a1 == "integral"):
                    damage = atk2["damage"]
                    if quick:
                        damage = int(damage * 1.25)
                    print(f"{p2} succeeded: {a2} deals {damage} to {p1}")
                    state[p1]["hp"] -= damage
                    if atk2.get("two_turn"):
                        state[p2]["pending"] += int(damage * 0.25)
                else:
                    selfd = int(atk2["damage"] * atk2.get("fail_self_mult", 0.5))
                    print(f"{p2} failed {a2}; takes {selfd} self-damage")
                    state[p2]["hp"] -= selfd
                if atk2.get("once_per_round"):
                    state[p2]["used_once"].add(a2)

            # clamp values and report
            state[p1]["hp"] = clamp(state[p1]["hp"]) 
            state[p2]["hp"] = clamp(state[p2]["hp"]) 
            state[p1]["brain"] = clamp(state[p1]["brain"], 0, 150)
            state[p2]["brain"] = clamp(state[p2]["brain"], 0, 150)

            print(f"After sequence {i+1}: {p1}: {state[p1]['hp']} HP, {state[p1]['brain']} brain || {p2}: {state[p2]['hp']} HP, {state[p2]['brain']} brain")

            # check end
            if state[p1]["hp"] <= 0 or state[p2]["hp"] <= 0:
                break

        round_no += 1

    # outcome
    print("\nGame over")
    print(f"Final: {p1}: {state[p1]['hp']} HP || {p2}: {state[p2]['hp']} HP")


if __name__ == "__main__":
    main()
