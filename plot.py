import matplotlib.pyplot as plt
import reduce_dimensions as RD

plt.figure(figsize=(11,8.5))
plt.plot(RD.tsne_results[:,0], RD.tsne_results[:,1], 'k.', markersize=2)

# plt.xticks([])
# plt.yticks([])

# Label all the sections
plt.rcParams.update({'font.size': 3})
for sec, id in RD.SR.word2id.items():
  plt.text(RD.tsne_results[id,0], RD.tsne_results[id,1], "§" + sec)

# plt.show()
plt.savefig('taxvectors_plot.pdf',
            format='pdf',
            bbox_inches="tight",
            tight_layout=True,
            orientation="landscape",
            papertype="letter")

plt.close()


# Start on the second diagram, focusing on Subchapter C
XRange = [13, 30]
YRange = [19,37]

plt.figure(figsize=(6,4))
plt.plot(RD.tsne_results[:,0], RD.tsne_results[:,1], 'k.', markersize=4)

plt.xticks([])
plt.yticks([])

# Label all the sections, if they are in the range we are plotting
plt.rcParams.update({'font.size': 8})
for sec, id in RD.SR.word2id.items():
    if XRange[0] <= RD.tsne_results[id, 0] <= XRange[1] and \
       YRange[0] <= RD.tsne_results[id, 1] <= YRange[1]:
        if sec == "1032":
            plt.annotate('§1032',
                         xy=(RD.tsne_results[id, 0], RD.tsne_results[id, 1]),
                         xytext=(RD.tsne_results[id, 0] + 2, RD.tsne_results[id, 1] + 2),
                         arrowprops=dict(arrowstyle="simple",
                                         connectionstyle="arc3,rad=-0.2",
                                         facecolor='black'
                                         ))
        else:
            halign = "left"
            valign = "center"
            if sec == "368":
                halign = "right"
            plt.text(RD.tsne_results[id,0]+0.08,
                     RD.tsne_results[id,1],
                     "§" + sec,
                     horizontalalignment=halign,
                     verticalalignment=valign)

subC = RD.SD.subchapters["Subtitle A—CHAPTER 1—||||Subchapter C—Corporate Distributions and Adjustments"]
for s in subC:
   plt.plot(RD.tsne_results[RD.SR.word2id[s],0], RD.tsne_results[RD.SR.word2id[s],1], 'r.', markersize=4)

plt.xlim(XRange)
plt.ylim(YRange)

plt.savefig('taxvectors_plot_SubC.tif',
            format='tif',
            dpi=600,
            # bbox_inches="tight",
            orientation="landscape",
            tight_layout=True,
            papertype="letter")

plt.close()
