# BasCalc — Calculus Battle

## Objectives
- Reduce your opponent's HP to 0 before yours. A simultaneous 0 HP results in a double KO.

## Setup
- Initialize player names.
- HP: maximum 100.
- Brainpower: maximum 150.

## Main loop / Gameplay
- The game uses rounds; each round contains 3 turns. Turns occur simultaneously.
- While both players have HP > 0, repeat rounds:
	- Show round header and current HP/Brainpower for both players.
	- Prompt both players for a validated 3-digit attack sequence (attack combinations are represented by 7 digits).
	- Each chosen attack corresponds to a calculus-based problem that must be solved (for example, the limits attack will pose a limits problem).
	- If the problem is solved incorrectly, the attack fails and a punishment is applied.
	- A speed bonus is applied for solving correctly within ~30–45 seconds.

### Turn resolution
- Resolve each round across three sub-sequences: execute each player's action, check brainpower costs/requirements, apply effects, print status, and check win conditions after each turn.
- Increment the round number and repeat until one or both players reach 0 HP.

## Attacks
### Attack 1 — Optimization (Strong Attack)
- Deals large damage.
- High brainpower cost; can only be used once per round.
- Bonus: increased damage via a multiplier when solved quickly.
- Failure: 75% of the attack damage is applied to self.

### Attack 2 — Derivative (Countered by Integral)
- Small damage unless the opponent used an integral-based counter.
- Bonus: applies an inverse debuff on the opponent when solved quickly.
- Failure: self-infliction of the inverse debuff or self-damage.

### Attack 3 — Integral (Counters Derivative)
- Deals 5 base damage; damage scales and applies a debuff if the opponent used a derivative attack.
- Bonus: can bypass a derivative attack but deals only 20% extra damage in that case.
- Failure: deals only 1 damage with no debuff.

### Attack 4 — Continuity (Stealth Mechanic)
- Enables stealth: opponents' attacks may miss. Stealth chance decreases each round (exponential/logarithmic decay).
- Can only be used once per round.
- Bonus: slows the decay of stealth chance when solved quickly.
- Failure: vulnerability next turn (damage taken is doubled).

### Attack 5 — Limits (Regeneration)
- Heals the user progressively (limit-approaching heal) until the round ends.
- Bonus: applies a defense buff when solved quickly.
- Failure: applies a defense debuff and reduces healing.

### Attack 6 — Chain Rule (Buff/Debuff System)
- Grants attack and defense buffs that chain, up to 3 levels.
- One buff level decays per round.
- Bonus: buff effect is doubled for the next turn when solved quickly.
- Failure: applies attack and defense debuffs.

### Attack 7 — Definite Integral (Two-Turn Attack)
- Deals large damage and spans two turns: it stores a fraction of damage received and releases it on the next turn.
- Bonus: when solved quickly, the attack fires immediately.
- Failure: self-damage and consumes all your turns in the round.

## Resources / References
- Calculus concepts used:
	- Limits
	- Derivatives & chain rule
	- Integrals (including definite integrals)
	- Function continuity
	- Optimization
