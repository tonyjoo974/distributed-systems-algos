import sys


HOST_COUNT = int(sys.argv[1]) + 1

for i in range(1, int(HOST_COUNT)):
   with open("config_"+str(i)+"_"+str(HOST_COUNT-1)+".txt", 'w') as config_file:
       config_file.write(f"{int(HOST_COUNT)-2}\n")
       for j in range(1, int(HOST_COUNT)):
            if i != j:
                config_file.write(f"node{j} fa21-cs425-g47-0{j}.cs.illinois.edu {j}077")
                if j != HOST_COUNT-1:
                    config_file.write("\n")
                    