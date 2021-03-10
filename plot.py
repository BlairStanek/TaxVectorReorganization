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

print("Full size:", RD.tsne_results.shape)

plt.close()


# Start on the second diagram, focusing on Subchapter C
XRange = [13, 30]
YRange = [19,37]

plt.figure(figsize=(6,4))
plt.plot(RD.tsne_results[:,0], RD.tsne_results[:,1], 'k.', markersize=4)

plt.xticks([])
plt.yticks([])

GENERAL_FONT_SIZE = 8
SEC1032_FONT_SIZE = 12

# Label all the sections, if they are in the range we are plotting
plt.rcParams.update({'font.size': GENERAL_FONT_SIZE})
for sec, id in RD.SR.word2id.items():
    if XRange[0] <= RD.tsne_results[id, 0] <= XRange[1] and \
       YRange[0] <= RD.tsne_results[id, 1] <= YRange[1]:
        if sec == "1032":
            plt.rcParams.update({'font.size': SEC1032_FONT_SIZE})
            plt.annotate('§1032',
                         xy=(RD.tsne_results[id, 0], RD.tsne_results[id, 1]),
                         xytext=(RD.tsne_results[id, 0] + 2, RD.tsne_results[id, 1] + 2),
                         arrowprops=dict(arrowstyle="simple",
                                         connectionstyle="arc3,rad=0.2",
                                         facecolor='black'
                                         ))
            plt.rcParams.update({'font.size': GENERAL_FONT_SIZE})
        else:
            halign = "left" # default
            if sec in ["368", "382", "453B", "1366", "1059", "316", "381",
                       "312", "357", "301", "306", "356", "351", "304"]:
                halign = "right"
            elif sec in ["381", "346", "311", "336", "337", "356", "354"]:
                halign = "center"

            valign = "center" # default
            extra_pad = 0.0
            pad_space = "\u2009"
            if sec in ["368", "382", "1368", "1374", "724", "383",
                       "311", "355", "336", "337", "351"]:
                valign = "top" # dot is on the top
                extra_pad = 0.1
                pad_space = ""
            elif sec in ["381",  "1366", "1363", "1367", "453B", "316",
                         "544", "384", "346", "269A", "331", "356", "354"]:
                valign = "bottom" # dot is on the bottom
                pad_space = ""

            if sec == "506": # manual adjustment
                extra_pad = 0.1
            if sec == "351": # manual adjustment
                extra_pad = -0.1


            plt.text(RD.tsne_results[id,0], # +0.08,
                     RD.tsne_results[id,1] - extra_pad,
                     pad_space + "§" + sec + pad_space,
                     horizontalalignment=halign,
                     verticalalignment=valign)

subC = RD.SD.subchapters["Subtitle A—CHAPTER 1—||||Subchapter C—Corporate Distributions and Adjustments"]
for s in subC:
   plt.plot(RD.tsne_results[RD.SR.word2id[s],0], RD.tsne_results[RD.SR.word2id[s],1],
            'o', markersize=3, color='black', markerfacecolor='red', markeredgewidth=0.3)

plt.xlim(XRange)
plt.ylim(YRange)

plt.savefig('taxvectors_plot_SubC.tif',
            format='tif',
            dpi=800,
            # bbox_inches="tight",
            orientation="landscape",
            tight_layout=True,
            papertype="letter")

plt.close()
