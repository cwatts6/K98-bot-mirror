# Simple tester for kingdom_summary helper functions
# Run: python -m stats_alerts.testers_only.test_kingdom_summary

from stats_alerts.embeds import kingdom_summary as ks


def show_case(curr, prev, label, invert=False):
    d = ks.compute_delta(curr, prev)
    ind = ks.indicator_for_change(d, invert_for_rank=invert)
    print(
        f"{label}: current={curr}, prev={prev} -> delta={d}, indicator={ind}, pretty_current={ks.pretty_num(curr)}"
    )


def main():
    print("=== Kingdom Summary helper tests ===")
    # numeric increase
    show_case(1200000, 1150000, "Kingdom Power")
    # numeric decrease
    show_case(9500, 10000, "Total Deads")
    # same
    show_case(5000, 5000, "KP")
    # no previous
    show_case(12345, None, "CH25")
    # rank: lower is better (improvement)
    show_case(3, 5, "Kingdom Rank", invert=True)
    show_case(7, 7, "Kingdom Rank (same)", invert=True)
    show_case(9, 6, "Kingdom Rank (worse)", invert=True)


if __name__ == "__main__":
    main()
