import pstats

stats = pstats.Stats("profile.prof")

stats.sort_stats("cumulative")
stats.print_stats(30)