# ddd = {'a': True, 'b': True, 'c': True}
# print(ddd.items())
# print(ddd)


free_spots = [[True for _ in range(10)] for _ in range(10)]
free_spots[0][0] = False
for i in range(2):
    for j in range(2):
        free_spots[2+i][2+j] = False
for line in free_spots:
    print(line)
