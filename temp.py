dd = dict()
for i in range(10):
    dd[i] = 10*i

for key, val in dd.items():
    if key == 4:
        del(dd[key])

print(dd)
