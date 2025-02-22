import sys
print(f'{sys.version = }')
print(f'{sys.platform = }')
print()

import mymod
print(mymod.lib.add(4, 6))
