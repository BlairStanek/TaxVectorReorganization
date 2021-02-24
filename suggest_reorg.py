# This file uses vector semantics to suggest ways to renumber some sections of the tax code
import subdivs as SD # This module opens the official IRC XML file and extracts the hierarchy
import numpy
import sys

VOCAB_CUTOFF = 30  # do not suggest removing sections if they appear below this number
                   # of times in the corpus

THRESHOLD_DATA_COUNT = 100  # only consider moving sections to or from a subdivision
                            # if the sections in that subdivision have over this number
                            # of appearances in the corpus

THRESHOLD_IMPROVEMENT = 0.01 # only suggest improvements if they are above this

DELIMIT_STRING = "||||"  # This is used to delimit the full IRC structure in text

# This function reads the section vectors and other info into these global variables
all_embeddings = []
word2id = {}
vocab_count = {}
def read_vectors():
    global all_embeddings

    # For this, use the TaxVectors file available from https://doi.org/10.7281/T1/N1X6I4
    FILE_PATH = "/Users/andrew/Desktop/RESEARCH/CPL TaxVectorSemantics/tax_15win_feb25.txt"
    print("Reading vectors from: ", FILE_PATH)
    f=open(FILE_PATH, "r") # read only!
    line = f.readline().strip().split(' ')
    assert len(line) == 2
    vocab_size = int(line[0])
    dimension = int(line[1])
    print("Vocab Size = ", vocab_size, "  Dimension = ", dimension)
    idx = 0
    num_lines = 0

    sect_dict = SD.get_section_dict() # This gets the definitive list of sections from the official IRC XML file

    for line in f.readlines():
        num_lines += 1
        if line[:4] == "sec_":  # we need only those vectors that start with sec_
            line=line.strip().split()
            word=line[0]
            if word[4:].upper() in sect_dict:
                embedding=[float(x) for x in line[1:]]
                assert len(embedding)==dimension
                all_embeddings.append(embedding)
                word2id[word[4:].upper()]=idx
                idx += 1
    f.close()
    assert num_lines == vocab_size
    all_embeddings=numpy.array(all_embeddings) # convert to numpy for easy computation
    print("Shape of sections vectors is ", all_embeddings.shape)

    # Read in the vocab count file, which is relevant for getting a
    # sense for how much data we have on each section.
    # You can get this file from the DOI repository
    VOCAB_COUNT_FILE_PATH = "/Users/andrew/Desktop/RESEARCH/CPL TaxVectorSemantics/vocab_count_feb25.txt"
    vocab_count_file = open(VOCAB_COUNT_FILE_PATH, "r")
    for line in vocab_count_file.readlines():
        line = line.strip().split()
        assert len(line) == 2, "Should be word then count for each line"
        if line[0][:4] == "sec_": # we need only those vectors that start with sec_
            vocab_count[line[0][4:].upper()] = int(line[1])
    vocab_count_file.close()


def cosine(x, y):
    return (numpy.sum(x * y)) / (numpy.sqrt(numpy.sum(x * x)) * numpy.sqrt(numpy.sum(y * y)))

cached_cosines = {} # key is tuple of (str, str), where the first str < second str
def get_cosine(word1: str, word2:str) -> float:
    tup = (word1, word2)
    if word1 > word2:
        tup = (word2, word1)
    if tup in cached_cosines:
        return cached_cosines[tup]
    idx1 = word2id[word1]
    idx2 = word2id[word2]
    embedding1 = all_embeddings[idx1:idx1 + 1]
    embedding2 = all_embeddings[idx2:idx2 + 1]
    cos_value = cosine(embedding1, embedding2)
    cached_cosines[tup] = cos_value
    return cos_value

# Helper function to get a list of the items in the subdivision closest the the
# candidate section.
def build_list_distances_and_counts(candidate:str, sec_list, sec_to_exclude_list) -> list:
    rv = []
    for sec in sec_list:
        if sec not in sec_to_exclude_list:
            if sec in word2id and sec != candidate:
                rv.append((sec, get_cosine(candidate, sec), vocab_count[sec]))
    rv.sort(reverse=True, key=lambda x: x[1]) # sort based on cosine
    return rv

def sum_counts(l:list) -> int:
    rv = 0
    for name, cos, count in l:
        rv += count
    return rv

# The metric used is the average distance of the two closest sections.
# We assume that the list is already sorted.
def dist_2closest(l:list) -> float:
    return (l[0][1] + l[1][1])/2.0

# This takes a subdivision's identifying string and puts it into readable format for display
def pretty_print_subdivision(subdivs:dict, subdiv_name:str) -> str:
    list_sections = subdivs[subdiv_name]
    if subdiv_name.find(SD.IDENTITY_SUBCHAPTER_ID) > 0:
        short_name = subdiv_name[:subdiv_name.find(DELIMIT_STRING)][:-2] + " (Chapter has no Subchapters)"
    else:
        short_name = subdiv_name.replace(DELIMIT_STRING, "")
    return short_name + " (§§ " + list_sections[0] + "-" + list_sections[-1] + ")"


# This function does the actual comparisons and printouts
def calculate_sections_to_move(subdivs:dict):

    exclude_list = [] # these are the sections that we want to exclude from Destination calculations

    move_list = [] # this contains the list of proposed moves

    for run_index in ["first", "second"]:
        total_sections = 0
        sections_with_better = 0

        for subdiv_source in subdivs.keys():

            source_seclist = subdivs[subdiv_source]
            for candidate in source_seclist: # consider moving this candidate
                if candidate in word2id and vocab_count[candidate] >= VOCAB_CUTOFF:  # must have sufficient data on section itself

                    source_list = build_list_distances_and_counts(candidate, source_seclist, []) # never exclude from source
                    count_source_list = sum_counts(source_list)
                    if count_source_list > THRESHOLD_DATA_COUNT and \
                            len(source_list) > 2:  # must have sufficient data on section's subdivision
                        total_sections += 1

                        list_better =[]  # list of tuples of all better subdivisions

                        # loop thru all other subdivisions looking for a better fit for the candidate
                        for subdiv_dest in subdivs.keys():
                            if subdiv_dest != subdiv_source: # don't move from itself to itself!

                                dest_seclist = subdivs[subdiv_dest]
                                exclude = []
                                if run_index == "second":
                                    exclude = exclude_list

                                dest_list = build_list_distances_and_counts(candidate, dest_seclist, exclude)
                                count_dest_list = sum_counts(dest_list)
                                if count_dest_list > THRESHOLD_DATA_COUNT and \
                                        len(dest_list) > 2: # must have sufficient data on the possible subdivision we'd move to

                                    source_wavg = dist_2closest(source_list)
                                    dest_wavg = dist_2closest(dest_list)

                                    if dest_wavg > (source_wavg + THRESHOLD_IMPROVEMENT): # then move!
                                        desc_str = "\t" + subdiv_dest + " §" + dest_seclist[0] + " to §" + dest_seclist[-1] + "\n"
                                        desc_str += "\t source = {0:.6f}  dest = {1:.6f}\n".format(source_wavg, dest_wavg)
                                        desc_str += "\t\t " + str(dest_list)
                                        list_better.append((dest_wavg - source_wavg, subdiv_dest, desc_str))

                        if len(list_better) > 0:
                            list_better.sort(reverse=True, key=lambda x: x[0])
                            sections_with_better += 1
                            if run_index == "first":
                                exclude_list.append(candidate) # exclude outliers from the second run
                            if run_index == "second" :
                                move_list.append((candidate,
                                                  vocab_count[candidate],
                                                  subdiv_source,
                                                  list_better[0][1], # best destination subdivision
                                                  list_better[0][0]  # improvement of dest over source
                                                  ))

    # print out the possible moves
    move_list.sort(key=lambda x: x[4], reverse=True)
    for i in range(len(move_list)):

        print("§{:10s} |{:20s} |{:30s} |{:30s} |{:.3f} |{:8d}".format(move_list[i][0],
                                   SD.sect_name_dict[move_list[i][0]],
                                   pretty_print_subdivision(subdivs, move_list[i][2]),
                                   pretty_print_subdivision(subdivs, move_list[i][3]),
                                   move_list[i][4],
                                   vocab_count[move_list[i][0]]
                                   ))

if __name__ == "__main__":
    SD.populate_subdivision_lists(DELIMIT_STRING) # reads the section hierarchy from the official IRC
    read_vectors() # loads the vectors and vocab counts
    print("Chapters:")
    calculate_sections_to_move(SD.chapters)
    print("Subchapters:")
    calculate_sections_to_move(SD.subchapters)
    print("Parts:")
    calculate_sections_to_move(SD.parts)
    print("Subparts:")
    calculate_sections_to_move(SD.subparts)


