# ------------------------------------------------------------------------------
#
#   Copyright 2018-2019 Fetch.AI Limited
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------
from typing import List

from fetchai.ledger.api import LedgerApi
from fetchai.ledger.contract import SmartContract
from fetchai.ledger.crypto import Entity, Address

EXAMPLE_INPUT_HISTORICS = "1233.64, 1236.12, 1243.01, 1259.7, 1257.02, 1266.79, 1261.43, 1258.02, 1263.72, 1279.74, 1271.91, 1273.34, 1274.35, 1273.39, 2742.99, 2737.98, 2744.62, 2741.39, 2741.39, 2744.56, 2738.81, 2737.69, 2740.18, 2741.84, 2746.43, 2752.4, 2757.27, 2753.97, 2743.49, 2751.33, 2743.44, 2869.05, 2868.62, 2867.16, 2866.54, 2865.44, 2861.87, 2860.77, 2860.59, 2863.89, 2853.05, 2854.79, 2857.21, 2854.82, 2853.04, 2863.73, 2862.9, 2862.91, 2864.06, 2862.42, 2858.14, 2863.41, 2862.38, 2859.34, 2859.39, 2859.35, 2867.37, 2869.51, 2865.43, 2869.09, 2871.42, 2866.52, 2867.44, 2863.21, 2860.28, 2855.86, 2859.58, 2866.15, 2866.15, 2864.66, 2865.5, 2858.29, 2861.95, 2866.69, 2863.14, 2869.23, 1570.21, 1563.2, 1564.64, 1562.1, 1559.03, 1558.86, 1558.01, 1557.89, 1556.76, 1559.78, 1555.93, 1559.99, 1558.2, 1560.13, 1560.08, 1561.08, 1558.01, 1555.68, 1557.34, 1558.19, 1557.82, 1562.66, 1563.46, 1562.64, 1562.64, 1562.63, 1562.12, 1558.49, 1556.2, 1556.68, 1558.39, 1556.24, 1556.82, 1278.19, 1393.52, 1392.96, 1394.44, 1397.78, 1400.37, 1400.53, 1401.99, 1403.26, 1402.03, 1401.93, 1053.31, 1051.27, 1049.12, 1048.25, 1046.69, 1046.96, 1047.9, 1048.08, 1046.69, 1044.26, 1044.83, 1044.83, 1045.3, 1043.55, 1035.62, 1037.24, 1037.17, 1032.22, 1025.38, 1026.55, 1030.86, 1030.5, 1028.24, 1028.07, 1027.24, 1025.69, 1025.87, 1027.98, 1028.34, 1029.45, 1027.82, 1027.82, 1029.65, 1033.75, 1033.54, 1032.43, 1032.21, 889.735, 890.573, 889.335, 889.057, 887.474, 885.708, 885.198, 885.229, 886.037, 884.4, 882.524, 878.074, 879.898, 882.436, 880.53, 882.546, 882.897, 882.88, 885.555, 888.409, 889.566, 887.182, 894.329, 907.583, 905.168, 902.77, 911.609, 909.893, 915.968, 922.051, 915.868, 918.69, 919.437, 917.056, 913.179, 914.791, 919.279, 924.188, 925.496, 925.572, 691.851, 690.559, 692.911, 693.258, 629.552, 627.839, 628.183, 627.839, 629.35, 628.487, 627.707, 626.481, 627.94, 626.472, 625.794, 628.345, 628.248, 628.758, 628.348, 628.483, 629.26, 629.362, 643.31, 642.885, 643.6, 651.552, 649.815, 650.445, 652.41, 652.453, 653.775, 654.235, 652.393, 652.393, 652.279, 650.932, 650.936, 650.285, 651.09, 652.872, 654.13, 654.172, 653.907, 651.571, 812.75, 812.801, 813.615, 813.983, 809.586, 807.437, 809.148, 809.15, 809.837, 808.116, 805.628, 805.747, 810.219, 809.485, 810.122, 806.982, 808.571, 806.224, 805.635, 808.571, 814.362, 810.552, 811.678, 813.086, 811.051, 812.49, 812.029, 809.998, 811.542, 810.902, 811.54, 808.578, 808.031, 807.003, 807.177, 808.324, 808.759, 808.174, 809.511, 807.788, 807.657, 807.788, 806.741, 806.699, 804.948, 805.697, 803.444, 803.496, 806.142, 803.547, 803.547, 802.657, 803.464, 803.141, 802.969, 803.429, 803.525, 804.751, 802.186, 804.468, 806.084, 804.961, 805.654, 806.514, 807.395, 807.122, 806.693, 806.693, 808.004, 807.989, 807.526, 806.686, 806.701, 807.094, 805.727, 805.131, 3090.23, 3092.62, 3090.2, 3087.19, 3088.64, 3090.32, 3075.09, 3085.48, 3077.04, 3073.65, 3076.15, 3074.63, 3079.8, 3076.32, 3853.59, 3833.22, 3833.89, 3845.16, 3839.13, 3841.19, 3838.29, 3840.88, 3841.13, 3847.67, 3855.05, 5407.2, 21992.4, 21884.9, 21886.4, 21926.5, 21902.8, 21930.7, 21931.7, 21944.6, 21967.1, 21967.1, 22015.6, 22003.7, 21908.2, 21938.5, 21934.8, 5486.65, 2210.14, 2205.57, 2209.81, 2208.41, 2211.32, 2212.73, 2216.77, 2212.36, 2214.02, 2213.86, 2214.31, 2215.23, 2214.28, 2214.31, 2213.98, 2217.2, 2213.81, 2208.81, 2207.65, 2202.52, 2208.76, 2210.84, 2207.32, 2206.87, 2212.46, 2211.44, 2214.72, 2210.26, 2211.55, 2214.11, 2208.76, 2210.93, 2208.19, 2213.68, 2214.98, 2214.38, 2214.38, 2214.99, 2441.87, 2440.87, 2226.27, 2222.09, 2193.45, 2198.18, 2178.85, 2183.74, 2184.45, 2182.65, 2192.02, 2194.09, 2193.51, 2191.61, 2185.96, 2190.46, 2185.58, 2186.15, 2192.73, 2190.89, 2188.05, 2177.58, 2183.5, 2179.61, 2181.74, 2178.79, 2180.1, 2180.2, 2185.51, 2185.53, 2188.98, 2187.24, 2184.89, 2185.14, 2184.77, 2181.49, 2182.04, 2179.45, 2178.34, 2176.18, 2180.88, 2181.01, 2185.56, 2183.01, 2186.44, 1285.99, 1286.16, 1292.25, 1289.29, 1289.41, 1289.41, 1288.55, 1286.58, 1286.96, 1288.38, 1287.8, 1289.29, 1288.94, 1289.95, 1293.38, 1289.63, 1291.07, 1289.2, 1287.82, 1290.33, 1298.23, 1298.02, 1296.96, 1297.86, 1295.54, 1295.54, 1296.44, 1294.9, 1293.33, 1291.85, 1291.85, 1289.33, 1288.41, 1284.3, 1286.83, 1285.29, 1287.55, 1290.83, 1293.15, 1291.63, 1289.26, 1290.88, 1293.47, 1291.14, 1293.89, 1293.89, 1290.66, 1290.48, 1292.68, 1293, 1293, 1293.45, 1290.39, 1290.47, 1290.33, 1290.3, 1291.34, 1290.3, 1291.76, 1291.63, 1292.77, 1293.43, 1292.77, 1292.6, 1291.76, 1288.16, 1288.67, 1286.72, 1286.72, 1276.86, 1275.19, 1281.52, 1278.89, 1282.75, 1282.94, 1283.19, 1277.42, 1277.78, 1276.19, 1280.74, 936.02, 936.783, 938.019, 936.487, 935.628, 936.162, 936.958, 935.251, 933.614, 935.241, 935.164, 935.11, 932.19, 928.731, 929.416, 929.966, 931.982, 931.053, 923.692, 924.917, 918.443, 923.578, 749.073, 752.335, 750.736, 748.071, 748.921, 749.961, 750.929, 751.939, 750.267, 748.079, 751.285, 754.13, 751.098, 751.857, 751.433, 750.037, 751.842, 751.977, 753.626, 751.355, 750.792, 750.704, 749.137, 750.054, 750.909, 751.115, 751.102, 752.321, 750.807, 751.159, 751.189, 751.164, 751.228, 756.141, 755.959, 754.896, 754.835, 756.896, 756.613, 756.909, 755.982, 572.797, 573.812, 573.14, 573.17, 573.087, 573.083, 571.363, 571.047, 571.566, 570.987, 571.67, 571.67, 571.651, 569.312, 569.35, 570.035, 652.303, 654.945, 654.072, 654.403, 654.945, 655.054, 655.434, 654.412, 655.866, 654.727, 655.498, 654.522, 655.199, 655.271, 655.271, 654.859, 655.873, 657.455, 657.946, 656.921, 695.286, 696.018, 696.007, 696.472, 694.424, 693.843, 694.748, 692.952, 692.996, 694.721, 697.012, 696.634, 694.223, 694.37, 696.151, 694.548, 696.034, 696.151, 696.151, 696.232, 696.024, 696.957, 697.7, 696.271, 694.379, 695.849, 695.861, 694.763, 695.891, 694.647, 693.026, 692.937, 693.19, 694.479, 694.417, 694.464, 693.476, 693.64, 694.478, 694.595, 694.595, 694.537, 695.119, 695.834, 695.857, 694.42, 695.848, 694.725, 695.104, 695.11, 695.784, 694.836, 695.784, 695.786, 697.304, 697.204, 697.534, 697.585, 697.404, 698.541, 696.312, 697.097, 697.52, 1774.79, 1772.85, 1768.76, 1768.33, 1766.57, 1768.57, 1769.51, 1770.09, 1770.78, 1771.01, 1767.49, 1763.34, 1763.33, 1768.63, 1767.21, 1770.18, 1772.35, 1773.02, 1772.44, 1766.86, 1766.93, 1772.15, 1770.97, 1768.34, 1760.74, 1762.1, 1760.92, 1759.78, 1750.43, 1755.84, 1752.3, 1752.36, 1750.03, 2326.25, 2318.56, 2322.38, 2322.07, 2322.84, 2320.04, 2326.92, 2325.15, 2326.83, 2325.91, 2322.07, 2321.29, 2321.29, 2328.86, 2326.81, 2326.59, 2326.55, 2325.57, 2322.84, 2322.86, 2324.21, 2323.74, 2316.23, 3479.6, 3469.42, 3462.39, 3457.46, 3471.46, 3465.56, 3457.73, 3464.32, 3464.32, 3460.82, 3485.01, 3479.77, 3479.64, 3483.82, 3516.79, 3555.35, 7156.16, 7163.95, 7173.78, 7149.42, 7128.83, 7134.83, 7156.13, 7148.2, 7157.76, 7144.38, 7151.03, 7159.41, 7162.12, 7168.05, 7177.31, 7174.21, 7178.01, 7178.01, 7171.15, 7144.4, 7143.27, 7153.32, 7163.27, 7140.29, 7154.8, 7142.77, 7155.96, 7155.84, 7156.07, 7143.53, 7151.54, 7134.84, 7147.06, 7123.11, 7144.42, 7145.46, 7143.11, 7138.6, 7144.17, 7155.44, 7155.42, 7165.38, 7155.87, 7161.86, 7155.09, 7174.84, 7167.89, 7162.01, 7163.2, 7171.51, 7162.34, 3562.76, 3571.16, 3564.6, 3577.47, 3564.86, 3568.74, 3295.02, 3295.9, 3292.49, 3293.74, 3293.74, 3298.48, 3304.95, 3304.95, 3305.64, 2251.09, 2255.86, 2254.78, 2252.21, 2250.02, 2254.75, 2254.75, 2254.34, 2249.41, 2242.53, 2242.54, 2242.63, 2243.77, 2244.54, 2242.61, 2238.55, 2244.21, 2237.75, 2243.95, 2236.66, 2238.56, 2238.48, 2243.52, 2243.69, 2243.89, 2243.89, 2243.49, 2245.13, 2244.51, 2244.58, 2242.62, 2245.5, 2238.36, 2246.64, 2244.85, 2245.15, 2248.62, 2247.34, 726.918, 726.453, 726.263, 725.992, 725.989, 725.989, 726.006, 726.067, 726.692, 726.944, 726.993, 727.047, 727.065, 727.065, 727.065, 726.084, 726.312, 726.312, 727.712, 726.825, 726.834, 726.882, 727.386, 726.882, 726.882, 727.395, 727.55, 727.55, 727.514, 728.337, 728.099, 728.099, 727.566, 726.772, 726.494, 724.273, 725.497, 726.958, 726.992, 726.958, 726.981, 728.628, 728.885, 728.885, 727.781, 728.187, 913.575, 913.12, 911.963, 911.585, 911.596, 911.538, 931.153, 929.105, 929.13, 929.161, 930.789, 929.448, 929.62, 929.62, 931.17, 996.555, 994.394, 994.516, 995.964, 994.856, 996.524, 995.719, 996.333, 995.81, 996.441, 997.21, 997.584, 997.316, 996.735, 998.435, 997.356, 998.571, 997.94, 999.937, 998.811, 998.912, 999.125, 999.615, 1002.04, 1002.37, 1000.23, 998.221, 997.638, 994.954, 995.8, 995.475, 988.979, 989.792, 945.563, 945.718, 944.474, 944.804, 946.762, 947.814, 945.566, 949.122, 947.049, 946.76, 946.494, 947.116, 945.717, 944.784, 944.784, 946.066, 946.044, 947.141, 945.587, 945.231, 946.436, 944.69, 944.006, 945.671, 945.589, 945.561, 944.366, 942.982, 944.939, 944.939, 944.939, 944.816, 944.784, 945.095, 945.095, 945.133, 945.133, 945.554, 945.09, 942.932, 941.393, 941.287, 939.916, 935.609, 939.831, 941.937, 940.493, 940.493, 940.26, 941.518, 943.012, 943.367, 941.184, 940.741, 941.746, 941.056, 941.054, 940.089, 941.187, 940.183, 938.719, 941.186, 942.14, 941.753, 941.237, 941.64, 939.216, 939.481, 939.483, 941.168, 940.214, 940.948, 941.784, 941.784, 941.784, 939.105, 941.057, 943.039, 944.858, 944.868, 946.494, 944.863, 945.561, 946.328, 944.861, 946.372, 944.915, 944.871, 944.162, 944.159, 943.141, 943.147, 945.126, 944.991, 944.78, 942.861, 943.419, 1033.48, 1036.29, 1034.95, 1034.99, 1034.94, 1034.97, 1034.98, 1035.25, 1035.29, 1035.96, 1035.58, 1035.63, 1035.94, 1036.1, 1037.12, 1037.12, 1037.16, 1037.12, 1038.52, 1038.24, 1038.32, 1040.7, 1038.29, 1038.89, 1039, 1039.57, 1040.18, 1039.57, 1040.94, 1041.66, 1039.83, 1038.56, 1035.54, 1035.1, 1033.48, 1032.71, 1035.49, 1034.92, 1035.48, 1033.84, 1034.34, 1035.66, 1033.43, 1033.32, 1033.39, 1033.28, 1035.66, 1035.38, 1035.89, 1035.68, 1033.26, 1033.82, 1032.47, 1034.25, 1034.92, 1034.94, 1034.3, 1034.36, 1035.55, 1035.55, 1036.01, 1036.33, 1032.44, 1032.67, 1033.11, 1032.75, 1032.9, 1032.28, 1030.92, 1029.34, 1029.19, 1026.15, 1023.63, 1026.39, 1025.77, 1025.84, 1027.47, 1026.13, 1025.95, 1027.66, 1027.9, 1026.43, 1024.93, 1024.76, 1027.16, 1025.59, 1024.2, 1024.22, 1025.91, 1024.07, 1019.44, 1015.88, 1019.15, 1018.78, 1018.39, 1018.49, 1024.93, 1022.19, 1020.25, 1023.22, 1022.76, 1023.18, 1022.08, 1020.79, 1020.39, 1020.16, 1021.23, 1022.19, 1020.66, 1021.23, 1023.48, 1022.91, 1022.36, 1024.92, 1023.39, 1022.67, 1022.52, 1022.37, 1022.35, 1022.52, 1022.33, 1024.54, 1024.41, 1023.84, 1022.52, 1021.27, 1019.66, 1019.72, 1019.81, 1019.67, 1019.99, 1020.06, 1020.33, 1020.45, 1020.7, 1019.92, 1019.92, 1017.08, 1019.24, 1018.74, 1018.57, 1018.67, 1019.91, 1023.95, 1025.36, 1024.95, 1023.83, 1022.86, 1023.91, 1022.79, 1023.42, 1022.14, 1022.14, 1023.41, 1023.3, 1024.37, 1024.46, 1025.35, 1024.7, 4236.22, 4231.3, 4236.36, 4230.73, 4235.89, 4230.73, 4230.73, 4230.73, 4230.73, 4230.9, 4238.98, 4229.86, 4233.14, 4233.61, 4236.86, 4236.86, 4227.45, 4227.25, 4234.96, 4236.86, 4231.99, 4235.72, 4245.69, 4245.62, 4279.07, 4260.12, 4256.19, 4259.02, 4259.26, 4256.3, 4256.31, 4258.16, 4258.27, 4255.87, 4255.37, 4255.85, 4245.95, 4252.65, 4258, 4250.7, 4247.02, 4241.37, 4238.54, 4238.53, 4231.51, 4232.64, 4228.53, 4237.35, 4230.37, 4230.74, 4229.38, 4232.2, 4222.34, 4215.47, 4219.14, 4217.4, 4215.33, 4210.56, 4225.34, 4215.78, 4224.44, 4227.05, 6984.05, 6988.41, 6984.14, 6986.03, 6987.11, 6997.8, 6997.42, 6989.88, 3222.41, 2146.36, 2148.75, 2149.15, 2149.13, 2148.43, 2152.01, 1783.9, 1781.91, 1781.56, 1778.61, 1778.78, 1783.11, 1784.12, 1784.75, 1783.91, 1783.7, 1784.43, 1784.63, 1429.06, 1429.4, 1429.78, 1429.78, 1429.06, 1429.09, 1426.68, 1431.21, 1431.66, 1435.29, 1434.41, 1438.11, 1436.21, 1433.59, 1432.09, 1432.06, 1434.96, 1434.78, 1435.02, 1434.69, 1432.96, 1435.12, 1438.62, 1437.33, 1437.33, 1436.61, 1435.32, 1435.96, 1483.55, 1481.43, 1481.46, 1483.07, 1479.69, 1479.33, 1477.89, 1482.56, 1484.04, 1515.99, 1507.14, 1506.82, 1507.73, 1508.32, 1504.67, 1502.65, 1497.63, 1502.42, 1501.44, 1502.46, 1504.12, 1497.75, 1499.92, 1499.92, 1500.51, 1500.73, 1500.68, 1498.15, 1500.49, 1497.75, 1498.34, 1498.13, 1498.37, 1498.67, 1498.4, 1497.78, 1495.72, 1495.9, 1494.3, 1493.8, 1493.85, 1495.39, 1493.22, 1496, 1495.51, 1492.82, 1495.63, 1498.52, 1496.2, 1498.16, 1497.87, 1497.91, 1500.26, 1500.37, 1501.44, 1475.06, 1474.11, 1474.99, 1472.77, 1431.83, 1431.75, 1091.65, 1090.25, 1090.14, 1090.16, 1090.14, 1033.6, 1034.66, 1036.56, 1034.2, 1033.61, 1032.23, 1032.23, 1032.23, 1033.87, 1033.67, 1032.45, 1032.96, 1034.51, 1033.44, 1032.12, 1182.13, 1181.37, 1179.48, 1180.43, 1179.4, 1180.7, 1181.67, 1181.68, 1181.69, 1183.15, 1184.85, 1183.12, 1184.38, 1182.5, 1182.62, 1185.08, 1185.08, 1185.13, 1185.08, 1183.82, 1184, 1182.68, 1183.81, 1181.89, 1183.81, 1182.64, 1183.81, 1182.81, 1183.13, 1182.81, 1182.68, 1182.68, 1181.93, 1181.93, 1181.99, 1182.05, 1182.32, 1184.82, 1183.13, 1183.29, 1184.56, 1182.15, 1182.12, 1180.43, 1177.48, 1176.97, 1177.25, 1181.03, 1176.91, 1175.72, 1176.25, 1178.1, 1178.12, 1177.46, 1095.83, 1095.76, 1095.76, 1095.76, 1193.85, 1193.85, 1196.33, 1196.42, 2060.94, 2060.98, 2063.83, 2063.82, 2061.87, 2061.87, 2064.47, 2060.94, 2064.36, 2064.14, 2062.08, 2057.53, 2055.46, 2056.68, 2059.57, 2061.89, 2061.95, 2061.95, 2064.52, 2064.15, 2061.01, 2060.55, 2058.78, 2062.85, 2059.31, 2062.79, 2059.37, 2054.42, 2056.09, 2053.95, 2058.45, 2054.08, 2054.9, 2054.82, 2050.7, 2053.66, 2056.94, 2054.89, 2056.61, 2052.74, 2056.09, 2056.09, 2058.17, 1603.54, 1602.57, 1602.57, 1601.9, 1604.98, 1604.99, 1606.41, 1607.69, 1607.43, 1605.38, 1605.38, 1603.26, 1605.05, 1608.28, 1604.19, 1608.12, 1605.2, 1608.19, 1607.94, 1607.43, 1607.43, 1606.17, 1606.09, 1606.17, 1607.67, 1607.09, 1609.24, 1609.24, 1607.12, 1611.43, 1607.66, 1606.92, 1606.92, 1605.88, 1605.13, 1608.16, 1609.55, 1605.85, 1610.25, 1614.84, 1613.19, 1611.27, 1615.74, 1618.43, 1620.48, 1617.92, 1616.36, 1615.36, 1612.13, 1612.91, 1615.85, 1539.21, 1542.04, 1540.64, 1542.25, 1543.47, 1544.81, 1541.12, 1546.7, 1547.2, 1552.34, 1550.15, 1551.77, 1562.55, 1554.19, 1554.08, 1553.23, 1554.02, 1554.48, 1554.48, 1552.53, 1549.54, 1547.67, 1546.68, 1545.19, 1620.14, 1621.11, 1623.87, 1623.56, 1621.86, 1624.11, 1619.66, 1619.27, 1622.73, 1620.95, 1621.8, 1619.28, 1621.24, 1620.16, 1621.8, 1623.86, 1624.37, 1623.59, 1621.9, 1622.29, 1620.9, 1621, 1614.74, 1614.73, 1610.02, 1604.76, 1610.02, 1608.4, 1611.52, 1614.09, 1611.28, 1611.41, 1615.13, 1615.14, 1612.99, 1618.76, 1618.66, 1617.12, 1613.28, 1612.4, 1612.42, 1612.55, 1612.44, 1614.09, 1612.5, 1614.96, 1615.08, 1616.83, 1616.37, 1616.35, 1616.34, 1616.41, 1614.85, 1614.2, 1614.14, 1616.25, 1614.15, 1614.35, 1616.28, 1616.13, 1616.14, 1614.91, 1614.14, 1614.14, 1614.15, 1614.15, 1618.36, 1621.7, 1621.71, 1621.71, 1623.8, 1621.81, 667.035, 665.7, 666.508, 665.978, 507.916, 503.185, 501.334, 501.183, 500.596, 501.02, 500.587, 500.842, 501.972, 501.972, 501.972, 501.474, 502.416, 502.161, 502.662, 502.693, 503.147, 503.092, 503.012, 502.932, 502.662, 502.567, 502.565, 501.792, 503.595, 503.216, 503.589, 503.106, 503.651, 503.563, 503.092, 503.093, 503.332, 503.332, 503.333, 503.342, 503.675, 503.971, 504.411, 346.616, 346.507, 308.165, 308.002, 308.228, 308.238, 308.233, 306.86, 307.389, 307.207, 307.075, 307.187, 306.74, 305.063, 304.336, 302.807, 301.081, 300.419, 299.725, 300.081, 300.015, 300.319, 300.521, 300.76, 300.76, 300.864, 301.782, 301.458, 300.821, 301.05, 301.546, 300.806, 301.147, 300.759, 300.73, 301.038, 301.147, 301.108, 301.306, 301.352, 301.901, 301.568, 301.402, 301.225, 301.579, 301.576, 301.516, 301.838, 301.451, 301.449, 301.45, 301.254, 301.34, 300.384, 300.522, 300.668, 556.428, 557.005, 558.153, 558.095, 693.709, 693.764, 694.14, 694.152, 694.153, 695.431, 694.02, 694.107, 694.579, 694.692, 694.918, 694.142, 565.801, 477.943, 476.981, 477.001, 477.278, 478.037, 478.048, 446.813, 362.609, 362.517, 361.946, 362.091, 362.483, 363.888, 363.688, 363.606, 363.329, 363.509, 363.59, 363.092, 362.911, 362.935, 362.886, 363.258, 363.459, 362.958, 363.372, 593.192, 593.019, 677.266, 677.438, 675.742, 675.81, 677.062, 676.024, 677.185, 677.513, 676.928, 676.666, 676.884, 676.575, 676.418, 676.089, 677.144, 677.886, 677.959, 677.986, 677.423, 678.046, 677.88, 677.793, 676.791, 676.314, 675.639, 676.283, 677.29, 677.072, 676.418, 676.518, 675.172, 675.567, 676.946, 676.11, 676.09, 675.347, 675.324, 675.05, 675.194, 675.413, 675.594, 676.004, 676.889, 675.967, 676.293, 676.966, 676.329, 675.747, 675.657, 675.741, 676.878, 676.965, 676.346, 675.05, 675.05, 675.778, 675.105, 675.433, 675.817, 673.714, 675.547, 679.982, 686.482, 686.053, 686.675, 687.667, 687.979, 642.857, 642.714, 641.181, 706.564, 707.975, 708.367, 706.728, 706.755, 707.941, 708.596, 707.538, 707.538, 707.971, 707.609, 708.798, 709.171, 708.717, 707.836, 707.538, 708.575, 707.751, 707.638, 707.962, 708.623, 707.975, 708.037, 707.975, 709.794, 709.648, 710.671, 711.204, 711.388, 711.122, 712.184, 711.331, 709.435, 709.08, 708.786, 707.942, 707.939, 707.958, 572.995, 573.345, 572.995, 572.264, 571.759, 572.918, 573.32, 573.32, 573.312, 573.8, 573.782, 573.338, 485.216, 485.145, 485.199, 485.299, 485.948, 485.413, 485.112, 484.608, 484.512, 579.068, 575.16, 574.132, 451.058, 451.075, 451.749, 300.172, 300.284, 300.355, 300.066, 300.429, 300.428, 300.593, 299.696, 299, 299.81, 299.81, 299.933, 299.921, 300.389, 299.858, 299.905, 299.89, 300.079, 300.048, 299.572, 299.581, 299.667, 299.936, 299.515, 299.515, 299.725, 299.078, 299.257, 299.078, 297.99, 298.628, 299.159, 298.368, 298.333, 298.906, 298.445, 298.13, 298.282, 298.281, 298.476, 298.745, 299.048, 299.069, 299.529, 299.721, 299.565, 299.781, 299.563, 299.618, 300.351, 299.777, 299.903, 299.942, 300.166, 300.286, 300.387, 299.867, 299.857, 300.162, 300.341, 299.933, 300.553, 300.51, 300.51, 299.857, 299.751, 299.917, 300.027, 300.495, 300.179, 300.181, 299.561, 299.756, 300.207, 300.207, 300.207, 300.207, 300.207, 300.449, 300.62, 301.162, 301.333, 301.438, 301.19, 301.333, 301.167, 301.214, 301.271, 301.813, 301.857, 301.333, 301.478, 301.083, 301.508, 300.883, 300.881, 300.867, 315.86, 315.862, 420.813, 420.901, 420.892, 420.971, 421.207, 421.187, 421.067, 420.608, 420.7, 420.277"

CONTRACT_TEXT = """

persistent graph_state : Graph;
persistent dataloader_state : DataLoader;
persistent optimiser_state : Optimiser;
persistent historics_state : Tensor;

// Smart contract initialisation sets up our graph, dataloader, and optimiser
// in this example we hard-code some values such as the expected input data size
// we could, however, easily add new methods that overwrite these values and 
// update the dataloader/optimiser as necessary
@init
function setup(owner : Address)

  use graph_state;
  use dataloader_state;
  use optimiser_state;
  use historics_state;

  var owner_balance = State<UInt64>(owner);
  owner_balance.set(1000000u64);

  // initial graph construction
  var g = graph_state.get(Graph());
  graphSetup(g);
  graph_state.set(g);
  
  // initial dataloader construction
  var dl = dataloader_state.get(DataLoader("tensor"));
  dataloader_state.set(dl);
  
  // initial optimiser setup
  var optimiser = optimiser_state.get(Optimiser("sgd", g, dl, "Input", "Label", "Error"));
  optimiser_state.set(optimiser);
  
  // intial historics setup
  var tensor_shape = Array<UInt64>(3);
  tensor_shape[0] = 1u64;                 // data points are spot price, so size == 1
  tensor_shape[1] = 2048u64;              // previous 2048 data points
  tensor_shape[2] = 1u64;                 // batch size == 1
  var historics = historics_state.get(Tensor(tensor_shape));
  historics_state.set(historics);
  
endfunction

// Method initial graph setup (we could forgo adding ops/layers
// if the graph would later be set via a call to updateGraph)
function graphSetup(g : Graph)

    // set up the computation graph
    var conv1D_1_filters        = 16;
    var conv1D_1_input_channels = 1;
    var conv1D_1_kernel_size    = 377;
    var conv1D_1_stride         = 3;
    
    var keep_prob_1 = 0.5fp64;
    
    var conv1D_2_filters        = 8;
    var conv1D_2_input_channels = conv1D_1_filters;
    var conv1D_2_kernel_size    = 48;
    var conv1D_2_stride         = 2;
    
    g.addPlaceholder("Input");
    g.addPlaceholder("Label");
    g.addConv1D("hidden_conv1D_1", "Input", conv1D_1_filters, conv1D_1_input_channels,
                    conv1D_1_kernel_size, conv1D_1_stride);
    g.addRelu("relu_1", "hidden_conv1D_1");
    g.addDropout("dropout_1", "relu_1", keep_prob_1);
    g.addConv1D("Output", "dropout_1", conv1D_2_filters, conv1D_2_input_channels,
                            conv1D_2_kernel_size, conv1D_2_stride);
    g.addMeanSquareErrorLoss("Error", "Output", "Label");
endfunction

// Method to set new historics as data changes
@action
function setHistorics(new_historics: String)
    use historics_state;
    var historics = historics_state.get();
    historics.fromString(new_historics);
    historics_state.set(historics);
endfunction

// Method to make a single prediction based on currently set historics
@action
function makePrediction() : String
    use graph_state;
    use historics_state;
    
    var g = graph_state.get();
    var historics = historics_state.get();

    g.setInput("Input", historics);
    var prediction = g.evaluate("Output");
    
    prediction.squeeze();

    return prediction.toString();

endfunction

// Method for overwriting the current graph
// this can be used either to update the weights
// or to replace with a totally new model
@action
function updateGraph(graph_string : String)
    use graph_state;
    var g = graph_state.get();
    g = g.deserializeFromString(graph_string);
    graph_state.set(g);
endfunction

// method to train the existing graph with current historics data
// labels must be provided
@action
function train(train_labels_string: String)
    use historics_state;
    use graph_state;
    use dataloader_state;
    use optimiser_state;
    
    // retrieve the latest graph
    var g = graph_state.get();
    
    // retrieve the historics
    var historics = historics_state.get();
 
    // retrieve dataloader
    var dataloader = dataloader_state.get();
    
    // add the historics as training data, and add provided labels
    var train_labels : Tensor;
    train_labels.fromString(train_labels_string);
    dataloader.addData(historics, train_labels);
     
    // retrieve the optimiser
    var optimiser = optimiser_state.get();
    optimiser.setGraph(g);
    optimiser.setDataloader(dataloader);
 
    var training_iterations = 1;
    var batch_size = 8u64;
    for(i in 0:training_iterations)
        var loss = optimiser.run(batch_size);
    endfor
endfunction


"""

def main():

    # create our first private key pair
    entity1 = Entity()

    # build the ledger API
    api = LedgerApi('127.0.0.1', 8100)

    # create wealth so that we have the funds to be able to create contracts on the network
    api.sync(api.tokens.wealth(entity1, 1000000000000000))

    # create the smart contract
    contract = SmartContract(CONTRACT_TEXT)

    # deploy the contract to the network
    api.sync(api.contracts.create(entity1, contract, 1000000000))

    # set one real example input data set
    fet_tx_fee = 100000000
    api.sync(contract.action(api, 'setHistorics', fet_tx_fee, [entity1], EXAMPLE_INPUT_HISTORICS))

    # make a prediction
    fet_tx_fee = 1000000000

    # TODO - how to get return value here?
    api.sync(contract.action(api, 'makePrediction', fet_tx_fee, [entity1]))

if __name__ == '__main__':
    main()
