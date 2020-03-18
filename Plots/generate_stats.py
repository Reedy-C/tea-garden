import os
import csv
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("seaborn")

#remove x characters at the beginning of file names to make plots more readable
leading_remove = 13
#maximum generation
gen_limit = 20
#iteration/run used per file
its = ["0", "0", "0", "0", "0",
       "0", "0", "0", "0", "0"]

its_dict = {}
file_list = []

for f in os.listdir():
    if not f.startswith('.'):
        if f[-4:] == ".csv":
            if not f[-13:] == "gene data.csv":
                file_list.append(f)
        
for f in range(len(file_list)):
    its_dict[file_list[f]] = its[f]

#all functions call on a list of .csv files in the folder
#do not go over 10 files + associated gene data .csv files
#and have an option to produce graphs with or without agents who died from
#being too inbred

#agent number in two graphs: total by file and total by generation
def nums(fs, keep_inbreds):
    results_gen = {}
    results_tot = {}
    for f in fs:
        gen_dict = {}
        for a in np.arange(0, gen_limit+1):
            gen_dict[a] = 0
        tot = 0
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if row["iteration"] == its_dict[f]:
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                gen_dict[int(row["generation"])] += 1
                                tot += 1
                        else:
                             gen_dict[int(row["generation"])] += 1
                             tot += 1
        results_gen[f[leading_remove:]] = gen_dict
        results_tot[f[leading_remove:]] = tot
    plt.bar(results_tot.keys(), results_tot.values())
    plt.xlabel("# of total agents, inbreds kept = " +
           str(keep_inbreds))
    plt.ylabel("# of agents")
    plt.savefig("# agents total, inbreds kept " + str(keep_inbreds) + ".png")
    plt.clf()
    for f in fs:
        plt.plot(list(results_gen[f[leading_remove:]].keys()),
                 list(results_gen[f[leading_remove:]].values()),
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("# of total agents by gen, inbreds kept = " +
           str(keep_inbreds))
    plt.ylabel("# of agents")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("# agents by gen, inbreds kept " + str(keep_inbreds) + ".png")
    plt.clf()

#avg. lifespan by generation
def lifespan(fs, keep_inbreds):
    results = {}
    for f in fs:
        life_dict = {}
        for a in np.arange(0, gen_limit+1):
            life_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if row["iteration"] == its_dict[f]:
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                life_dict[int(row["generation"])].append(
                                            int(row["age"]))
                        else:
                             life_dict[int(row["generation"])].append(
                                 int(row["age"]))
        avgs = []
        for a in np.arange(0, gen_limit+1):
            avgs.append(sum(life_dict[a])/len(life_dict[a]))
        results[f[leading_remove:]] = avgs
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.yticks(np.arange(0, 130000, 10000))
    plt.xlabel("Avg age at death by gen, inbreds kept = " +
               str(keep_inbreds))
    plt.ylabel("Avg age at death")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("avg age at death, inbreds kept " + str(keep_inbreds)
                + ".png")
    plt.clf()

#avg. mating attempts by generation
def mas(fs, keep_inbreds):
    results = {}
    for f in fs:
        mas_dict = {}
        for a in np.arange(0, gen_limit+1):
            mas_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if row["iteration"] == its_dict[f]:
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                mas_dict[int(row["generation"])].append(
                                            int(row["mating attempts"]))
                        else:
                             mas_dict[int(row["generation"])].append(
                                 int(row["mating attempts"]))
        avgs = []
        for a in np.arange(0, gen_limit+1):
            avgs.append(sum(mas_dict[a])/len(mas_dict[a]))
        results[f[leading_remove:]] = avgs
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Avg # mating attempts by gen, inbreds kept = " +
               str(keep_inbreds))
    plt.ylabel("Avg # mating attempts")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("avg mating attempts, inbreds kept " + str(keep_inbreds)
                + ".png")
    plt.clf()

#percent of agents who survived to a threshold value by generation
def surv(fs, keep_inbreds, thresh=500):
    results = {}
    for f in fs:
        surv_gen = {}
        for a in np.arange(0, gen_limit+1):
            surv_gen[a] = 0
        tot_gen = {}
        for a in np.arange(0, gen_limit+1):
            tot_gen[a] = 0
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if row["iteration"] == its_dict[f]:
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                tot_gen[int(row["generation"])] += 1
                                if int(row["age"]) > thresh:
                                    surv_gen[int(row["generation"])] += 1
                        else:
                             tot_gen[int(row["generation"])] += 1
                             if int(row["age"]) > thresh:
                                 surv_gen[int(row["generation"])] += 1
        #save plots
        survs = []
        for a in np.arange(0, gen_limit+1):
            survs.append(surv_gen[a]/tot_gen[a])
        results[f[leading_remove:]] = survs
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Survival to age " + str(thresh) +
               " by gen, inbreds kept = " + str(keep_inbreds))
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Percent survived to age " + str(thresh))
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("percent survival to " + str(thresh) + " ticks, inbreds kept"
                + str(keep_inbreds) + ".png")
    plt.clf()

#avg. parent relatedness in two graphs: genetic overlap and degree of relation
def parent_overlaps(fs, keep_inbreds):
    result_overlaps = {}
    result_degrees = {}
    for f in fs:
        overlap_dict = {0: [0]}
        degree_dict = {0: [0]}
        for a in np.arange(1, gen_limit+1):
            overlap_dict[a] = []
            degree_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if row["iteration"] == its_dict[f]:
                    if int(row["generation"]) > 0 and\
                        int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                overlap_dict[int(row["generation"])].append(
                                            float(row["parent_genoverlap"]))
                                degree_dict[int(row["generation"])].append(
                                            float(row["parent_degree"]))
                        else:
                            overlap_dict[int(row["generation"])].append(
                                float(row["parent_genoverlap"]))
                            degree_dict[int(row["generation"])].append(
                                float(row["parent_degree"]))
        #save plots
        overlap_avgs = []
        degree_avgs = []
        for a in np.arange(0, gen_limit+1):
            overlap_avgs.append(sum(overlap_dict[a])/len(overlap_dict[a]))
            degree_avgs.append(sum(degree_dict[a])/len(degree_dict[a]))
        result_overlaps[f[leading_remove:]] = overlap_avgs
        result_degrees[f[leading_remove:]] = degree_avgs
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 result_overlaps[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Genetic overlap by gen, inbreds kept = " + str(keep_inbreds))
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Avg % genetic overlap")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("avg parent genoverlap, inbreds kept " + str(keep_inbreds)
                + ".png")
    plt.clf()
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 result_degrees[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Parental degree of relatedness by gen, inbreds kept = " +
               str(keep_inbreds))
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Avg degree relatedness")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("avg parent degree relatedness, inbreds kept " + str(keep_inbreds)
                + ".png")
    plt.clf()
    
#Nei's genetic diversity by generation
#may take a while to run
def nei_diversity(fs, keep_inbreds):
    results = {}
    for f in fs:
        fields = {}
        hjs = {}
        H = {}
        tot = [0 for a in np.arange(0, gen_limit+1, 1)]
        f2 = f[:-4] + " gene data.csv"
        for a in np.arange(0, gen_limit+1, 1):
            hjs[a] = []
            H[a] = 0
            fields[a] = {}
        with open(f2) as file:
            r = csv.DictReader(file)
            for n in r.fieldnames:
                if n[-6:] == "weight":
                    for a in np.arange(0, gen_limit+1, 1):
                        fields[a][n] = {}
        with open(f) as file:
            r = csv.DictReader(file)
            with open(f2) as file2:
                    r2 = csv.DictReader(file2)
                    file.seek(0)
                    row = next(r)
                    for row2 in r2:
                        while row2["agent_ident"] != row["ID"]:
                            try:
                                row = next(r)
                            except StopIteration:
                                file.seek(0)
                        if not keep_inbreds or \
                           row["cause of death"] != "Inbred":
                            if int(row["generation"]) <= gen_limit:
                                fields, tot = collect_fields(fields, row2,
                                                             tot,
                                                             int(row[
                                                                 "generation"]))
                                row2 = next(r2)
                                fields, tot = collect_fields(fields, row2,
                                                             tot,
                                                             int(row[
                                                                 "generation"]))
        tot_loci = len(fields[0].keys())
        for gen in fields:
            for loc in fields[gen]:
                freqs = []
                for allele in fields[gen][loc]:
                    freqs.append((fields[gen][loc][allele]/tot[gen])**2)
                #hj = 1 - SUM(allele freq)^2
                hjs[gen].append(1 - sum(freqs))
            vals = []
            for g in hjs[gen]:
                vals.append(g/tot_loci)
            #H = SUM(hj/TOTNUMloci)
            H[gen] = sum(vals)
        results[f[leading_remove:]] = H
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 list(results[f[leading_remove:]].values()),
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Nei's genetic diversity by gen, inbreds kept = " +
               str(keep_inbreds))
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Nei's diversity")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    plt.savefig("nei's genetic diversity, inbreds kept " + str(keep_inbreds)
                + ".png")
    plt.clf()

#helper function for nei_diversity
#collects alleles from one chromosome
def collect_fields(fields, row2, tot, gen):
    for key in fields[gen].keys():
        val = round(float(row2[key]), 2)
        if val in fields[gen][key].keys():
            fields[gen][key][val] += 1
        else:
            fields[gen][key][val] = 1
    tot[gen] += 1                                         
    return(fields, tot)
                

nums(file_list, True)
lifespan(file_list, True)
mas(file_list, True)
surv(file_list, True)
parent_overlaps(file_list, True)
nei_diversity(file_list, True)
print("Finished producing graphs")
