import suggest_reorg as SR
import subdivs as SD

# These do the mathematical transforms
from sklearn.decomposition import PCA
from sklearn.manifold import TSNE

# Other imports
import re

SD.populate_subdivision_lists(SR.DELIMIT_STRING)
SR.read_vectors()

pca = PCA(n_components=50, random_state=42) # setting random seed to 42 for reproducibility
pca_result = pca.fit_transform(SR.all_embeddings)
tsne = TSNE(n_components=2, verbose=1, perplexity=40, n_iter=1000, random_state=42) # setting random seed to 42 for reproducibility
tsne_results = tsne.fit_transform(pca_result)

results = []
for word, idx in SR.word2id.items():
    results.append((idx, word, tsne_results[idx,0], tsne_results[idx,1]))

def section_sort_key(x):
    m = re.match("\d+", x[1])
    sec_num = int(x[1][m.start():m.end()])
    return "{:04d}".format(sec_num) + x[1][m.end():]

if __name__ == "__main__":
    results.sort(key=section_sort_key) # sort by section number, with 16 appearing before 166
    for i in range(len(results)):
        print("§" + results[i][1], " , ", results[i][2], " , ", results[i][3])

