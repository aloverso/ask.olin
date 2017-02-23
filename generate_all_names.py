import random

f_emojis = open('emojis.txt')
emojis = f_emojis.readlines()
emojis = list(map(lambda n: n.strip(), emojis))
f_emojis.close()

f_adj = open('adjectives.txt')
adj = f_adj.readlines()
adj = list(map(lambda n: n.strip(), adj))
f_adj.close()

names = []

for ad in adj:
	for em in emojis:
		names.append("{}-{}".format(ad, em))

random.shuffle(names)

f_names = open('names.txt', 'w')
f_names.write("\n".join(names))