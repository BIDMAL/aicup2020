import numpy as np
import pprint
# aa = np.zeros((11, 11))
# size = 2
# radius = 3
# center = (5, 5)
# for i in range(size):
#     for j in range(size):
#         for xx in range(0, radius+1):
#             for yy in range(center[1]+j-radius+xx, center[1]+j+radius-xx+1):
#                 aa[center[0]+i+xx, yy] = 1
#                 aa[center[0]+i-xx, yy] = 1
#

size = 11
offset = 2
aa = np.zeros((size+2*offset, size+2*offset))
radius = 3
center = (5+offset, 5+offset)
for xx in range(0, radius+1):
    aa[center[0]+xx, center[1]-radius+xx:center[1]+radius-xx+1] = 1
    aa[center[0]-xx, center[1]-radius+xx:center[1]+radius-xx+1] = 1
print(aa)
aa = np.array(aa[offset:size+offset, offset:size+offset])
print(aa)
print(aa.shape)

# aa = np.zeros((80, 80))
# np.set_printoptions(threshold=np.inf)
# pp = pprint.PrettyPrinter(width=80, compact=False)
#
# print(aa)
