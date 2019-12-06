# This demo file contains all of the example code used in Zemla, Cao, Mueller, & Austerweil (under revision)

# These examples are used for exposition -- they use cases shown here are not
# always sensical. (For example, Example 3 uses an animal cluster scheme though
# not all the data is from the animal category; Example 4 uses letter fluency
# clusters though the data is not letter fluency data; etc.)

import snafu

# Example 1: Import data for the animal category of participant id A101
fluencydata_a101 = snafu.load_fluency_data("fluency_data/snafu_sample.csv", 
                                        subject="A101",
                                        category="animals", 
                                        spell="spellfiles/animals_snafu_spellfile.csv", 
                                        removePerseverations=True,
                                        scheme="schemes/animals_snafu_scheme.csv",
                                        removeIntrusions=True)

# Example 2: Import data for all categories of participants from group Experiment1 and Experiment2
fluencydata = snafu.load_fluency_data("fluency_data/snafu_sample.csv", 
                                        group=["Experiment1","Experiment2"],
                                        hierarchical=True)

# Example 3: Calculate the number of static cluster switches using an animal cluster scheme
#       - You may use another scheme file or create your own
#       - You can also use an integer in place of a scheme file to compute letter cluster switches (see Example 4)
#       - You may also use clustertype="fluid" (see Figure 1)
#       - Because the data is formatted hierarchically, the function calculates the number of switches per list and then averages over all lists per participant
#       - If the data are formatted non-hierarchically (set `hierarchical=False` in Example 2), it would return a meaure per-list instead of per-participant
#       - The same is true for other examples below
avg_num_cluster_switches = snafu.clusterSwitch(fluencydata.labeledlists, "schemes/animals_snafu_scheme.csv", clustertype="static")

# Example 4: Calculate the average fluid cluster size using the first two letters of a word as category labels (letter fluency)
#       - This example shows how to calculate letter fluency clusters; the parameter `2` specifies to use the first two letters of each word as a cluster label
#       - You can also use a scheme file in place of an integer to use semantic fluency clusters
avg_cluster_sizes = snafu.clusterSize(fluencydata.labeledlists, 2)

# Example 5: Calculate the number of perseverations in each list of the dataset.
#       - Perseverations are calculated *after* spell-corrections (see `spell` parameter of Example 1)
#       - This may be important, particularly for data collected online where participants misspell a word and then purposefully correct it on the next line
avg_num_perseverations = snafu.perseverations(fluencydata.labeledlists)

# Example 6: Return a list of perseverations found in each fluency list
#       - Perseverations are calculated *after* spell-corrections (see `spell` parameter of Example 1)
perseveration_list = snafu.perseverationsList(fluencydata.labeledlists)

# Example 7: Find the number of intrusions using an animal category scheme
avg_num_intrusions = snafu.intrusions(fluencydata.labeledlists, "schemes/animals_snafu_scheme.csv")

# Example 8: Return a list of all intrusions in animal fluency data
intrusions_list = snafu.intrusionsList(fluencydata.labeledlists, "schemes/animals_snafu_scheme.csv")

# Example 9: Return all intrusions in letter fluency data by specifying the target letter
#       - The target letter is not case sensitive
intrusions_list_letter = snafu.intrusionsList(fluencydata.labeledlists, "a")


# Example 10: Returns the average word frequency per list (or participant) and a list of words not factored into this calculation (when missing is set to None)
avg_word_freq = snafu.wordFrequency(fluencydata.labeledlists, data="frequency/subtlex-us.csv", missing=0.5)


