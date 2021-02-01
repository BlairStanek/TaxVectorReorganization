import subdivs as SD
import numpy
import sys


VOCAB_CUTOFF = 30  # do not suggest removing sections if they appear below this number
                   # of times in the corpus

THRESHOLD_DATA_COUNT = 100  # only consider moving sections to or from a subdivision
                            # if the sections in that subdivision have over this number
                            # of appearances in the corpus

THRESHOLD_IMPROVEMENT = 0.05

DELIMIT_STRING = "||||"  # This is used to delimit the full IRC structure in text

# This function reads the section vectors and other info into these global variables
all_embeddings = []
all_words = []
word2id = {}
vocab_count = {}
def read_vectors():
    global all_embeddings
    global all_words

    FILE_PATH = "/Users/andrew/Desktop/RESEARCH/CPL TaxVectorSemantics/tax_15win_feb25.txt"  # This is the best vector we have
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
                all_words.append(word)
                word2id[word]=idx
                idx += 1
    f.close()
    assert num_lines == vocab_size
    all_embeddings=numpy.array(all_embeddings) # convert to numpy for easy computation
    print("Size of sections vectors in ", all_embeddings.shape)

    # Read in the vocab_count file ################################
    # The vocab count is relevant for getting a sense for how much data we have on the
    vocab_count_file = open("/Users/andrew/Desktop/RESEARCH/CPL TaxVectorSemantics/vocab_count_feb25.txt", "r")
    for line in vocab_count_file.readlines():
        line = line.strip().split()
        assert len(line) == 2, "Should be word then count for each line"
        vocab_count[line[0]] = int(line[1])
    vocab_count_file.close()


def cosine(x, y):
    return (numpy.sum(x * y)) / (numpy.sqrt(numpy.sum(x * x)) * numpy.sqrt(numpy.sum(y * y)))

# def euclid_distance(x, y):
#     return numpy.sqrt(numpy.sum((x-y) ** 2))


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

def formal_name(xml_sec_name:str) -> str:
    return "sec_" + xml_sec_name.lower()

def formal_name_toprettyprint(sec_name:str) -> str:
    assert sec_name[0:4] == "sec_"
    return sec_name[4:].upper()


cached_magnitudes = {}
def get_magnitude(sec_name:str) -> float:
    if sec_name not in cached_magnitudes:
        idx = word2id[sec_name]
        embedding1 = all_embeddings[idx:idx + 1].reshape(500)
        cached_magnitudes[sec_name] = numpy.sqrt(numpy.sum(embedding1 ** 2))
        assert 0 < cached_magnitudes[sec_name]
    return cached_magnitudes[sec_name]

def build_list_distances_and_counts(sec:str, sec_list, sec_to_exclude_list) -> list:
    rv = []
    for ss in sec_list:
        if ss not in sec_to_exclude_list:
            formal_ss = formal_name(ss)
            if formal_ss in word2id and formal_ss != sec:
                rv.append((formal_ss, get_cosine(sec, formal_ss), vocab_count[formal_ss]))
    rv.sort(reverse=True, key=lambda x: x[1]) # sort based on cosine
    return rv

def sum_counts(l:list) -> int:
    rv = 0
    for name, cos, count in l:
        rv += count
    return rv


def dist_2closest(l:list) -> float:
    return (l[0][1] + l[1][1])/2.0


# This function does the actual comparisons and printouts
def counting_comparisons(subdivs:dict):

    subdiv_out_candidates = {}

    for run in ["first", "second"]:
        print("RUN ", run, "--------------------------------------")
        total_sections = 0
        sections_with_better = 0

        for subdiv_source in subdivs.keys():
            if run == "first":
                subdiv_out_candidates[subdiv_source] = []
            source_seclist = subdivs[subdiv_source]
            for candidate_num in source_seclist:
                candidate = formal_name(candidate_num)
                if candidate in word2id and vocab_count[candidate] >= VOCAB_CUTOFF:  # must have sufficient data on section itself

                    source_list = build_list_distances_and_counts(candidate, source_seclist, [])
                    count_source_list = sum_counts(source_list)
                    if count_source_list > THRESHOLD_DATA_COUNT and \
                            len(source_list) > 2:  # must have sufficient data on section's subdivision
                        total_sections += 1

                        print(candidate, "\t", SD.sect_name_dict[candidate_num],
                              "=======================")

                        list_better =[]  # list of tuples of all better subdivisions

                        # loop thru all other subdivisions looking for a better fit
                        for subdiv_dest in subdivs.keys():
                            if subdiv_dest != subdiv_source: # don't move from itself to itself!

                                if run == "first":
                                    exclude = []
                                elif run == "second":
                                    exclude = subdiv_out_candidates[subdiv_dest]
                                else:
                                    assert False

                                dest_seclist = subdivs[subdiv_dest]
                                dest_list = build_list_distances_and_counts(candidate, dest_seclist, exclude)
                                count_dest_list = sum_counts(dest_list)
                                if count_dest_list > THRESHOLD_DATA_COUNT and \
                                        len(dest_list) > 2: # must have sufficient data on the possible subdivision we'd move to

                                    source_wavg = dist_2closest(source_list)
                                    dest_wavg = dist_2closest(dest_list)

                                    if dest_wavg > (source_wavg + THRESHOLD_IMPROVEMENT):
                                        desc_str = "\t" + subdiv_dest + " §" + dest_seclist[0] + " to §" + dest_seclist[-1] + "\n"
                                        desc_str += "\t source = {0:.6f}  dest = {1:.6f}\n".format(source_wavg, dest_wavg)
                                        desc_str += "\t\t " + str(dest_list)

                                        list_better.append((dest_wavg, desc_str))
                        if len(list_better) > 0:
                            if run == "first": # store which are outliers
                                subdiv_out_candidates[subdiv_source].append(candidate_num) # store that we've found a better match
                            list_better.sort(reverse=True, key=lambda x: x[0])
                            print("\t", "******FOUND A BETTER MATCH!********")
                            for i in range(min(len(list_better),5)):
                                print("{0:3d}".format(i), end=" ")
                                print(list_better[i][1])
                            sections_with_better += 1
        print("END OF RUN", run, " total_sections = ", total_sections)
        print("END OF RUN", run, " sections_with_better =", sections_with_better)


if __name__ == "__main__":
    SD.populate_subdivision_lists(DELIMIT_STRING)
    read_vectors()
    counting_comparisons(SD.subchapters)


