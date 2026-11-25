"""Sdrerminalowe kasyno. Uruchom poleceniem python3 kasyno.py."""
import random
from collections import Counter
from itertools import combinations

RANKS = "23456789TJQKA"
NAMES = ("wysoka karta", "para", "dwie pary", "trójka", "strit",
         "kolor", "full", "kareta", "poker")


def deck():
    cards = [r + s for r in RANKS for s in "♠♥♦♣"]
    random.shuffle(cards)
    return cards


def show(cards):
    return "  ".join(c.replace("T", "10") for c in cards)


def choice(prompt, options):
    while True:
        answer = input(prompt + " > ").strip().lower()
        if answer in options:
            return answer
        print("Dostępne opcje:", ", ".join(options))


def stake(limit):
    while True:
        try:
            value = int(input(f"Stawka (1–{limit}, 0 = powrót) > "))
            if 0 <= value <= limit:
                return value
        except ValueError:
            pass
        print(f"Wpisz liczbę całkowitą od 0 do {limit}.")


def points(hand):
    return sum((2, 3, 4, 5, 6, 7, 8, 9, 10, 2, 3, 4, 11)[RANKS.index(c[0])]
               for c in hand)


def oczko(balance):
    print("Zbliż się do 21 punktów. Walet = 2, dama = 3, król = 4, as = 11.")
    print("Dwa asy na start to perskie oczko, najwyższy wynik. Krupier dobiera do 17.")
    bet = stake(balance)
    if not bet:
        return balance
    cards = deck()
    player = [cards.pop(), cards.pop()]
    dealer = [cards.pop(), cards.pop()]
    print("Odkryta karta krupiera:", show(dealer[:1]))
    print("Twoje karty:", show(player), " | Punkty:", points(player))
    if points(player) == 22 or points(dealer) == 22:
        # Jedynie dwa asy dają 22 punkty w dwóch kartach.
        print("Perskie oczko!")
        result = int(points(player) == 22) - int(points(dealer) == 22)
    else:
        while points(player) < 21:
            if choice("[d] dobierz  [s] stój", ("d", "s")) == "s":
                break
            player.append(cards.pop())
            print("Twoje karty:", show(player), " | Punkty:", points(player))
        if points(player) > 21:
            result = -1
        else:
            while points(dealer) < 17:
                dealer.append(cards.pop())
            p, d = points(player), points(dealer)
            result = 1 if d > 21 or p > d else -int(p < d)
    print("Krupier:", show(dealer), " | Punkty:", points(dealer))
    print({1: "Wygrywasz!", 0: "Remis.", -1: "Wygrywa krupier."}[result],
          f"Bilans rozdania: {bet * result:+d}")
    return balance + bet * result


def rank5(cards):
    values = sorted((RANKS.index(c[0]) + 2 for c in cards), reverse=True)
    groups = sorted(((n, v) for v, n in Counter(values).items()), reverse=True)
    counts = [n for n, _ in groups]
    ordered = tuple(v for _, v in groups)
    flush = len({c[1] for c in cards}) == 1
    straight = 0
    if values == [14, 5, 4, 3, 2]:
        straight = 5
    elif len(groups) == 5 and values[0] - values[-1] == 4:
        straight = values[0]
    if flush and straight:
        return (8, straight)
    if counts[0] == 4:
        return (7,) + ordered
    if counts == [3, 2]:
        return (6,) + ordered
    if flush:
        return (5,) + tuple(values)
    if straight:
        return (4, straight)
    category = {(3, 1, 1): 3, (2, 2, 1): 2, (2, 1, 1, 1): 1}
    return (category.get(tuple(counts), 0),) + ordered


def best(cards):
    return max(combinations(cards, 5), key=rank5)


def bot_move(hand, board, due, can_raise):
    if board:
        strong = rank5(best(hand + board))[0] >= 1
    else:
        strong = hand[0][0] == hand[1][0] or all(c[0] in "TJQKA" for c in hand)
    roll = random.random()
    if can_raise and roll < (0.40 if strong else 0.09):
        return "p"
    if due and not strong and roll > 0.78:
        return "f"
    return "s"


def betting(hand, board, total, bets, actor, unit, cap):
    """Zwraca numer pasującego lub None. Obaj grają do wspólnego limitu."""
    pending = 2
    increases = 0
    while pending and min(total) < cap:
        other = 1 - actor
        due = bets[other] - bets[actor]
        extra = min(unit, cap - total[actor] - due)
        can_raise = extra > 0 and increases < 2
        if actor == 0:
            print(f"Pula: {sum(total)}  |  Twoje wolne żetony: {cap - total[0]}")
            labels = {"s": f"sprawdź (+{due})" if due else "czekaj"}
            if due:
                labels["f"] = "pas"
            if can_raise:
                labels["p"] = f"podbij (wpłacasz {due + extra})" if max(bets) else f"postaw {extra}"
            action = choice("  ".join(f"[{k}] {v}" for k, v in labels.items()), labels)
        else:
            action = bot_move(hand, board, due, can_raise)
            if action == "p":
                print(f"Komputer zwiększa stawkę o {extra}.")
            elif action == "s":
                print("Komputer sprawdza." if due else "Komputer czeka.")
        if action == "f":
            print("Pasujesz." if actor == 0 else "Komputer pasuje.")
            return actor
        payment = due
        pending -= 1
        if action == "p":
            payment += extra
            increases += 1
            pending = 1
        bets[actor] += payment
        total[actor] += payment
        actor = other
    return None


def holdem(balance, button):
    print("Grasz przeciw komputerowi z takim samym stosem jak Twój.")
    print("Ciemne 1/2. Krok licytacji 2 przed i po flopie, potem 4.")
    print("W rundzie można zwiększyć stawkę dwa razy.")
    cards = deck()
    hands = [[cards.pop(), cards.pop()] for _ in range(2)]
    board = []
    total = [0, 0]
    total[button], total[1 - button] = 1, min(2, balance)
    print("Mała ciemna:", "Ty" if button == 0 else "komputer")
    print("Twoje karty:", show(hands[0]))
    for stage, count, unit in [("Preflop", 0, 2), ("Flop", 3, 2),
                               ("Turn", 1, 4), ("River", 1, 4)]:
        board.extend(cards.pop() for _ in range(count))
        print(f"\n{stage}", show(board))
        folded = betting(hands[1], board, total, [0, 0] if count else total.copy(),
                         1 - button if count else button, unit, balance)
        if folded is not None:
            return balance - total[0] + (sum(total) if folded == 1 else 0)
    print("Karty komputera:", show(hands[1]))
    scores = []
    for who, cards in zip(("Ty", "Komputer"), hands):
        five = best(cards + board)
        score = rank5(five)
        print(f"{who}: {NAMES[score[0]]}  |  {show(five)}")
        scores.append(score)
    if scores[0] == scores[1]:
        print("Remis. Dzielicie pulę.")
        return balance
    won = scores[0] > scores[1]
    print("Wygrywasz!" if won else "Wygrywa komputer.", f"Pula: {sum(total)}")
    return balance + (total[1] if won else -total[0])


def main():
    balance = 100
    button = 0
    print("KASYNO  ♠ ♥ ♦ ♣")
    while balance:
        print(f"\nTwoje żetony: {balance}")
        game = choice("[1] Oczko  [2] Texas Hold’em  [0] Wyjście", ("0", "1", "2"))
        if game == "0":
            return
        if game == "1":
            balance = oczko(balance)
        else:
            balance = holdem(balance, button)
            button = 1 - button
    print("Żetony się skończyły. Dzięki za grę!")


if __name__ == "__main__":
    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\nKoniec gry.")
