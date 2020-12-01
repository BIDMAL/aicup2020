# ddd = {'a': True, 'b': True, 'c': True}
# print(ddd.items())
# print(ddd)


# free_spots = [[True for _ in range(10)] for _ in range(10)]
# free_spots[0][0] = False
# for i in range(2):
#     for j in range(2):
#         free_spots[2+i][2+j] = False
# for line in free_spots[11:]:
#     print(line)

ll = [[None for _ in range(10)] for _ in range(10)]
for i in range(10):
    for j in range(10):
        ll[i][j] = str(i) + str(j)
for line in ll:
    print(line)
print('-----------------------------------')
for z in range(10):
    print(f'z = {z}')
    for i in range(z):
        print(ll[i][z], ll[z][i], end=' ')
    print(ll[z][z])
