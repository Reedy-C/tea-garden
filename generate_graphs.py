import os
import csv
import matplotlib.pyplot as plt
import numpy as np

plt.style.use("seaborn")

#SETTINGS
#remove x characters at the beginning of file names on graph keys
#useful to make plots more readable
leading_remove = 0
#maximum generation to be plotted
gen_limit = 50
#if set to True, will run through all iterations/runs
#up to the limit found in the first file
#and publish graphs based on each one
compare_all_its = True
#when grpahic all iterations, each graph will be labeled with the iteration #

#iteration/run used per file for up to ten files if compare_all_its == False
its = ["0", "0", "0", "0", "0",
       "0", "0", "0", "0", "0"]

#used for plotting where two_envs has been turned on
#will separate env 0 and env 1 into different plots
separate_envs = True

#sub-folder to dig up files from
#if set to "", defaults to current folder
retrieval_directory = "Plots"

#sub-folder to save files into
#if set to "", defaults to current folder
save_directory = "Plots"

#if run was made with inbreed_lim set below 1, too-inbred agents die at birth
#this setting will include them if True and not if False
#(has no effect in inbreed_lim was not used)
keep_inbred_agents = True

#end of settings

its_dict = {}
file_list = []

def gather_files():
    """Retrieve all files to work on.
    """
    if not f.startswith('.'):
        if f[-4:] == ".csv":
            if not f[-13:] == "gene data.csv":
                file_list.append(os.path.join(retrieval_directory, f))

if retrieval_directory == "":
    for f in os.listdir():
        gather_files()
else:
    for f in os.listdir(retrieval_directory):
        gather_files()
        
for f in range(len(file_list)):
    its_dict[file_list[f]] = its[f]


#all functions call on a list of .csv files in the folder
#do not go over 10 files + associated gene data .csv files
#and have an option to produce graphs with or without agents who died from
#being too inbred

def nums(fs, keep_inbreds, itera=None):
    """Produces two kids of graphs with agent numbers: total by file and
    total by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
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
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                gen_dict[int(row["generation"])] += 1
                                tot += 1
                        else:
                             gen_dict[int(row["generation"])] += 1
                             tot += 1
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        results_gen[f[leading_remove:]] = gen_dict
        results_tot[f[leading_remove:]] = tot
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    plt.bar(results_tot.keys(), results_tot.values())
    plt.xlabel("# of total agents")
    plt.ylabel("# of agents")
    if save_directory == "":
        plt.savefig("# agents total " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                 ("# agents total " + plotend)))
    plt.clf()
    for f in fs:
        plt.plot(list(results_gen[f[leading_remove:]].keys()),
                 list(results_gen[f[leading_remove:]].values()),
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("# of total agents by gen")
    plt.ylabel("# of agents")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("# agents by gen " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("# agents total " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            nums(fs, keep_inbreds, itera+1)

def lifespan(fs, keep_inbreds, itera=None):
    """Produces graphs with average lifespan by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
    results = {}
    for f in fs:
        life_dict = {}
        for a in np.arange(0, gen_limit+1):
            life_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                life_dict[int(row["generation"])].append(
                                            int(row["age"]))
                        else:
                             life_dict[int(row["generation"])].append(
                                 int(row["age"]))
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        avgs = []
        for a in np.arange(0, gen_limit+1):
            if len(life_dict[a]) != 0:
                avgs.append(sum(life_dict[a])/len(life_dict[a]))
            else:
                avgs.append(0)
        results[f[leading_remove:]] = avgs
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.yticks(np.arange(0, 130000, 10000))
    plt.xlabel("Avg age at death by gen")
    plt.ylabel("Avg age at death")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average age at death " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average age at death " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            lifespan(fs, keep_inbreds, itera+1)

def mas(fs, keep_inbreds, itera=None):
    """Produces graphs with average number of mating attempts by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
    results = {}
    for f in fs:
        mas_dict = {}
        for a in np.arange(0, gen_limit+1):
            mas_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                mas_dict[int(row["generation"])].append(
                                            int(row["mating attempts"]))
                        else:
                             mas_dict[int(row["generation"])].append(
                                 int(row["mating attempts"]))
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        avgs = []
        for a in np.arange(0, gen_limit+1):
            if len(mas_dict[a]) != 0:
                avgs.append(sum(mas_dict[a])/len(mas_dict[a]))
            else:
                avgs.append(0)
        results[f[leading_remove:]] = avgs
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Avg # mating attempts by gen")
    plt.ylabel("Avg # mating attempts")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average mating attempts " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average mating attempts " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            mas(fs, keep_inbreds, itera+1)

def disorders(fs, keep_inbreds, itera=None):
    """Produces graphs with average number of disorders by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
    results = {}
    for f in fs:
        dis_dict = {}
        for a in np.arange(0, gen_limit+1):
            dis_dict[a] = []
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
                    if int(row["generation"]) <= gen_limit:
                        if not keep_inbreds:
                            if row["cause of death"] != "Inbred":
                                dis_dict[int(row["generation"])].append(
                                            int(row["# disorders"]))
                        else:
                            dis_dict[int(row["generation"])].append(
                                            int(row["# disorders"]))
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        avgs = []
        for a in np.arange(0, gen_limit+1):
            if len(dis_dict[a]) != 0:
                avgs.append(sum(dis_dict[a])/len(dis_dict[a]))
            else:
                avgs.append(0)
        results[f[leading_remove:]] = avgs
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.yticks(np.arange(0, 1.3, 0.1))
    plt.xlabel("Avg # disorders by gen")
    plt.ylabel("Avg # disorders")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average # disorders " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average # disorders " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            disorders(fs, keep_inbreds, itera+1)

def surv(fs, keep_inbreds, thresh=500, itera=None):
    """Produces graphs with percentage of agents who survived to threhold value
    time-steps by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
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
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
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
            else:
                if compare_all_its == True and cont == False:
                    if int(row["iteration"]) == itera + 1:
                        cont = True
        #save plots
        survs = []
        for a in np.arange(0, gen_limit+1):
            if tot_gen[a] != 0:
                survs.append(surv_gen[a]/tot_gen[a])
            else:
                survs.append(0)
        results[f[leading_remove:]] = survs
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1), results[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Survival to age " + str(thresh) + " by gen")
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Percent survived to age " + str(thresh))
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Percent survival to " + str(thresh) + " ticks " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Percent survival to " + str(thresh) +
                                   " ticks " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            surv(fs, keep_inbreds, thresh, itera+1)
            
def parent_overlaps(fs, keep_inbreds, itera=None):
    """Produces two types of graphs of parental relatedness by generation:
    by genetic overlap and by degree of relation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
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
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
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
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        #save plots
        overlap_avgs = []
        degree_avgs = []
        for a in np.arange(0, gen_limit+1):
            if len(overlap_dict[a]) != 0:
                overlap_avgs.append(sum(overlap_dict[a])/len(overlap_dict[a]))
                degree_avgs.append(sum(degree_dict[a])/len(degree_dict[a]))
            else:
                overlap_avgs.append(0)
                degree_avgs.append(0)
        result_overlaps[f[leading_remove:]] = overlap_avgs
        result_degrees[f[leading_remove:]] = degree_avgs
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 result_overlaps[f[leading_remove:]],
                 label=f[leading_remove:-4])
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Genetic overlap by gen")
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Avg % genetic overlap")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average parent genoverlap " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average parent genoverlap " +
                                   plotend)))
    plt.clf()
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 result_degrees[f[leading_remove:]],
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Parental degree of relatedness by gen")
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Avg degree relatedness")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average parent degree relatedness " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average parent degree relatedness " +
                                   plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            parent_overlaps(fs, keep_inbreds, itera+1)
            
#may take a while to run
def nei_diversity(fs, keep_inbreds, itera=None):
    """Produces graphs of Nei's genetic diversity by generation.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
    results = {}
    for f in fs:
        tot0 = 0
        fields = {}
        hjs = {}
        H = {}
        tot = [0 for a in np.arange(0, gen_limit+1, 1)]
        fgen = f[:-4] + " gene data.csv"
        for a in np.arange(0, gen_limit+1, 1):
            hjs[a] = []
            H[a] = 0
            fields[a] = {}
        with open(fgen) as filegen2:
            rgen = csv.DictReader(filegen2)
            for n in rgen.fieldnames:
                if n[-6:] == "weight":
                    for a in np.arange(0, gen_limit+1, 1):
                        fields[a][n] = {}
        with open(f) as filegen:
            r = csv.DictReader(filegen)
            with open(fgen) as filegen2:
                rgen = csv.DictReader(filegen2)
                filegen.seek(0)
                for row in r:
                    if (itera == None and row["iteration"] == its_dict[f]) or\
                       (itera != None and int(row["iteration"]) == itera):
                        if not keep_inbreds or \
                               row["cause of death"] != "Inbred":
                            if int(row["generation"]) <= gen_limit:
                                row2 = next(rgen)
                                while row2["agent_ident"] != row["ID"]:
                                    try:
                                        row2 = next(rgen)
                                        row2 = next(rgen)
                                    except StopIteration:
                                        filegen.seek(0)
                                fields, tot = collect_fields(fields, row2,
                                                             tot,
                                                             int(row[
                                                                 "generation"]))
                                fields, tot = collect_fields(fields, row2,
                                                             tot,
                                                             int(row[
                                                                 "generation"]))
                    else:
                        if compare_all_its == True and cont == False:
                            if int(row["iteration"]) == itera + 1:
                                cont = True
        tot_loci = len(fields[0].keys())
        for gen in fields:
            if tot[gen] == 0:
                H[gen] = 0
            else:
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
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    for f in fs:
        plt.plot(np.arange(0, gen_limit+1, 1),
                 list(results[f[leading_remove:]].values()),
                 label=f[leading_remove:-4])
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.xlabel("Nei's genetic diversity by gen")
    plt.yticks(np.arange(0, 1.01, .1))
    plt.ylabel("Nei's diversity")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Nei's genetic diversity " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Nei's genetic diversity " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            nei_diversity(fs, keep_inbreds, itera+1)

#helper function for nei_diversity
def collect_fields(fields, row2, tot, gen):
    """Return alleles from one chromosome.
    """
    for key in fields[gen].keys():
        val = round(float(row2[key]), 2)
        if val in fields[gen][key].keys():
            fields[gen][key][val] += 1
        else:
            fields[gen][key][val] = 1
    tot[gen] += 1                                         
    return(fields, tot)

def preferences(fs, keep_inbreds, itera=None):
    """Produces two kinds of grpahs of phenotype matching preference by
    generation: one with average and one with all individual preferences.
    """
    if compare_all_its == True:
        cont = False
        if itera == None:
            itera = 0
    results = {}
    if separate_envs:
        results_1 = {}
    for f in fs:
        pref_dict = {}
        scatter_x = []
        scatter_y = []
        if separate_envs:
            pref_dict_1 = {}
            scatter_x_1 = []
            scatter_y_1 = []
        for a in np.arange(0, gen_limit+1):
            pref_dict[a] = []
            if separate_envs:
                pref_dict_1[a] = []
        #collect data
        with open(f) as file:
            r = csv.DictReader(file)
            for row in r:
                if (itera == None and row["iteration"] == its_dict[f]) or\
                   (itera != None and int(row["iteration"]) == itera):
                    if int(row["generation"]) <= gen_limit:
                        if separate_envs and row["env #"] == "1":
                            if not keep_inbreds:
                                if row["cause of death"] != "Inbred":
                                    r = float(row["preference"].split(\
                                        ",")[2][1:-1])
                                    pref_dict_1[int(row["generation"])].append(\
                                        r)
                            else:
                                r = float(row["preference"].split(",")[2][1:-1])
                                pref_dict_1[int(row["generation"])].append(r)
                        else:
                            if not keep_inbreds:
                                if row["cause of death"] != "Inbred":
                                    r = float(row["preference"].split(\
                                        ",")[2][1:-1])
                                    pref_dict[int(row["generation"])].append(r)
                            else:
                                r = float(row["preference"].split(",")[2][1:-1])
                                pref_dict[int(row["generation"])].append(r)
                else:
                    if compare_all_its == True and cont == False:
                        if int(row["iteration"]) == itera + 1:
                            cont = True
        avgs = []
        if separate_envs:
            avgs_1 = []
        #compute averages and make scatterplot coordinates
        for a in np.arange(0, gen_limit+1):
            if len(pref_dict[a]) != 0:
                avgs.append(sum(pref_dict[a])/len(pref_dict[a]))
                for g in pref_dict[a]:
                    scatter_x.append(a)
                    scatter_y.append(g)
            else:
                avgs.append(0)
            if separate_envs:
                if len(pref_dict_1[a]) != 0:
                    avgs_1.append(sum(pref_dict_1[a])/len(pref_dict_1[a]))
                    for g in pref_dict_1[a]:
                        scatter_x_1.append(a)
                        scatter_y_1.append(g)
                else:
                    avgs_1.append(0)
        if not separate_envs:
            results[f[leading_remove:]] = [avgs, scatter_x, scatter_y]
        else:
            results[f[leading_remove:] + " 0"] = [avgs, scatter_x, scatter_y]
            results_1[f[leading_remove:] + " 1"] = [avgs_1, scatter_x_1,
                                                    scatter_y_1]
    #ColorBrewer color scheme qualitative-12 # 1
    #adapted slightly to darken some of the paler colors
    colors = ['#77b4d4', '#1f78b4', '#a2d973', '#33a02c', '#f96e6c', '#e31a1c',
              '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']
    count=0
    if itera == None:
        plotend = ".png"
    else:
        plotend = " " + str(itera) + ".png"
    #create graphs
    #first scatter
    for f in fs:
        lab = f[leading_remove:-4]
        name = f[leading_remove:]
        if separate_envs:
            lab_1 = lab + " 1"
            name_1 = name + " 1"
            lab = lab + " 0"
            name = name + " 0"
        plt.scatter(results[name][1], results[name][2], s = 20, label=lab,
                    color=colors[count])
        count += 1
        if separate_envs and len(f) > 1:
            plt.scatter(results_1[name_1][1], results_1[name_1][2], s = 20,
                        label=lab_1, color=colors[count])
            count += 1
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.yticks(np.arange(-1, 1.1, .2))
    plt.xlabel("Preferences by gen")
    plt.ylabel("Preference")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    #default is too small resolution to see much
    fig = plt.gcf()
    fig.set_size_inches(18, 12)
    if save_directory == "":
        plt.savefig("Preference " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Preference " + plotend)))
    plt.clf()
    count=0
    #next averages
    for f in fs:
        lab = f[leading_remove:-4]
        name = f[leading_remove:]
        if separate_envs:
            lab_1 = lab + " 1"
            name_1 = name + " 1"
            lab = lab + " 0"
            name = name + " 0"
        plt.plot(np.arange(0, gen_limit+1, 1), results[name][0],
                 label=lab, color=colors[count], linewidth=3)
        count += 1
        if separate_envs and len(f) > 1:
            plt.plot(np.arange(0, gen_limit+1, 1), results_1[name_1][0],
                     label=lab_1, color=colors[count], linewidth=3)
            count += 1
    plt.xticks(np.arange(0, gen_limit + 1, 5))
    plt.yticks(np.arange(-1, 1.1, .2))
    plt.xlabel("Avg. preference by gen")
    plt.ylabel("Avg. preference")
    plt.legend(facecolor="white", edgecolor="black",
               framealpha=1, frameon=True)
    if save_directory == "":
        plt.savefig("Average preference " + plotend)
    else:
        plt.savefig(os.path.join(save_directory,
                                  ("Average preference " + plotend)))
    plt.clf()
    if compare_all_its:
        if cont:
            preferences(fs, keep_inbreds, itera+1)

            
nums(file_list, keep_inbred_agents)
lifespan(file_list, keep_inbred_agents)
mas(file_list, keep_inbred_agents)
disorders(file_list, keep_inbred_agents)
surv(file_list, keep_inbred_agents)
parent_overlaps(file_list, keep_inbred_agents)
nei_diversity(file_list, keep_inbred_agents)
preferences(file_list, keep_inbred_agents)
print("Finished producing graphs")
