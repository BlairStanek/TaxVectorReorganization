# This file is used to build up a list of sections and subchapters
import xml.etree.ElementTree as ET

# You need to change this file to point to your downloaded copy of Title 26
# You can download the most recent copy from https://uscode.house.gov/download/download.shtml
TITLE26_XML_FILE_PATH = "/Users/andrew/Desktop/Data/IRC/usc26.xml"

TITLE26_XMLPATH = "/us/usc/t26/s"

# Each of these will have as key the full name hierarchy-included name of the subdivision,
# plus the title of the subdivision.  The values will be a list of the sections within that
# subdivision.
subtitles = {}
chapters = {}
subchapters = {}
parts = {}
subparts = {}

status_statistics = {} # includes count on number of active, repealed, reserved, etc. sections

sect_name_dict = {}

# Given some unit (which may be any level of subdivision), return a list containing
# all sections in that subdivision.
def return_sections(unit, collect_status_statistics = False):
    rv = []
    for s in unit.iter('{http://xml.house.gov/schemas/uslm/1.0}section'):
        if s.get("identifier") is not None:
            id = s.get("identifier")
            assert id.find(TITLE26_XMLPATH) == 0
            num = id[len(TITLE26_XMLPATH):]

            if num.find(TITLE26_XMLPATH) >= 0:  # Sometimes two sections are squished together into one identifier= field
                pass
            # Here we manually correct some weird ranges of repealed statutes
            elif num == "54A...54F":
                pass
            elif num == "418...418D":
                pass
            elif num == "860H...860L":
                pass
            elif num == "1232...1232B":
                pass
            elif num == "1400...1400C":
                pass
            elif num == "1400E...1400J":
                pass
            elif num == "1400L...1400U–3":
                pass
            elif num.find("...") > 0:
                pass
            else:
                status = s.get("status", "none")
                if collect_status_statistics:
                    status_statistics[status] = 1 + status_statistics.get(status, 0)

                name = None
                heading = s.find('{http://xml.house.gov/schemas/uslm/1.0}heading')
                if heading is not None:
                    name = heading.text
                    name = name.strip()

                if name is not None:
                    assert (num not in sect_name_dict) or \
                           sect_name_dict[num] == name, \
                            "a section should always have the same name"
                    sect_name_dict[num] = name

                if s.get("status") is None:
                    rv.append(num)
                else:
                    assert s.get("status") != "operational", "Only one we expected"
    return rv


def iter_subparts(part, prefix_str, delimit_prefix):
    for subpart in part.iter('{http://xml.house.gov/schemas/uslm/1.0}subpart'):
        subpart_num = subpart.find('{http://xml.house.gov/schemas/uslm/1.0}num').text
        subpart_name = subpart.find('{http://xml.house.gov/schemas/uslm/1.0}heading').text

        # populate the list of all subparts
        stored_name = prefix_str + delimit_prefix + subpart_num + subpart_name
        assert stored_name not in subparts, "Should not already be there"
        subparts[stored_name] = return_sections(subpart)


def iter_parts(subchapter, prefix_str, delimit_prefix):
    for part in subchapter.iter('{http://xml.house.gov/schemas/uslm/1.0}part'):
        part_num = part.find('{http://xml.house.gov/schemas/uslm/1.0}num').text
        part_name = part.find('{http://xml.house.gov/schemas/uslm/1.0}heading').text

        # First, populate the list of all parts
        stored_name = prefix_str + delimit_prefix + part_num + part_name
        assert stored_name not in parts, "Should not already be there"
        parts[stored_name] = return_sections(part)

        # Second, populate all subdivisions underneath
        iter_subparts(part, prefix_str + part_num, delimit_prefix)


def iter_subchapters(chapter, prefix_str, delimit_prefix):
    # Note that there are chapters with no subchapters
    empty = True
    for subchapter in chapter.iter('{http://xml.house.gov/schemas/uslm/1.0}subchapter'):
        empty = False
        subchapter_num = subchapter.find('{http://xml.house.gov/schemas/uslm/1.0}num').text
        subchapter_name = subchapter.find('{http://xml.house.gov/schemas/uslm/1.0}heading').text

        # First, populate the list of all subchapters
        stored_name = prefix_str + delimit_prefix + subchapter_num + subchapter_name
        assert stored_name not in subchapters, "Should not already be there"
        subchapters[stored_name] = return_sections(subchapter)

        # Second, populate all subdivisions underneath
        iter_parts(subchapter, prefix_str + subchapter_num, delimit_prefix)

    if empty:  # then we create an identity subchapter consisting of the whole chapter
        stored_name = prefix_str + delimit_prefix + "IdentitySubchapter"
        assert stored_name not in subchapters, "Should not already be there"
        subchapters[stored_name] = return_sections(chapter) # populates with ALL sections in this chapter


def iter_chapters(subtitle, prefix_str, delimit_prefix):
    empty = True
    for chapter in subtitle.iter('{http://xml.house.gov/schemas/uslm/1.0}chapter'):
        empty = False
        chapter_num = chapter.find('{http://xml.house.gov/schemas/uslm/1.0}num').text
        chapter_name = chapter.find('{http://xml.house.gov/schemas/uslm/1.0}heading').text

        # First, populate the list of all chapters
        stored_name = prefix_str + delimit_prefix + chapter_num + chapter_name
        assert stored_name not in chapters, "Should not already be there"
        chapters[stored_name] = return_sections(chapter)

        # Second, populate all subdivisions underneath
        iter_subchapters(chapter, prefix_str + chapter_num, delimit_prefix)

    assert not empty, "Should be no empty chapters"


def iter_subtitles(title, delimit_prefix):
    empty = True
    for subtitle in title.iter('{http://xml.house.gov/schemas/uslm/1.0}subtitle'):
        empty = False
        subtitle_num = subtitle.find('{http://xml.house.gov/schemas/uslm/1.0}num').text
        subtitle_name = subtitle.find('{http://xml.house.gov/schemas/uslm/1.0}heading').text

        # First, populate the list of all subtitles
        stored_name = subtitle_num + subtitle_name
        assert stored_name not in subtitles, "Should not already be there"
        subtitles[stored_name] = return_sections(subtitle, True) # only time we collect sections

        # Second, populate all subdivisions underneath
        iter_chapters(subtitle, subtitle_num, delimit_prefix)

    assert not empty, "Should be no empty Subtitles"


# This does the work of actually opening the XML file and populating the various subdivision dictionaries
def populate_subdivision_lists(delimit_prefix=""):
    tree = ET.parse(TITLE26_XML_FILE_PATH)
    root = tree.getroot()
    iter_subtitles(root, delimit_prefix)


# Returns a dictionary of all sections that appear
def get_section_dict() -> dict:
    rv = {}
    for subtitle in subtitles.keys():
        for sec in subtitles[subtitle]:
            assert sec not in rv, "Should not have duplicates in subtitles"
            rv[sec] = None # add

    # Make sure all subdivisions' section lists are a subset of what we are returning
    for subdivs in [chapters, subchapters, parts, subparts]:
        for subdiv in subdivs.keys():
            for sec in subdivs[subdiv]:
                assert sec in rv, "Should be contained"

    # Make sure what we are returning matches a direct run of the XML
    tree = ET.parse(TITLE26_XML_FILE_PATH)
    root = tree.getroot()
    alt_copy = return_sections(root)
    assert len(rv) == len(alt_copy), "Should be same length"
    for sec1 in rv:
        assert sec1 in alt_copy
    for sec2 in alt_copy:
        assert sec2 in rv

    return rv


def print_subdivisions(subdiv_list, title_text):
    print("--------------------------------------")
    for subdiv in subdiv_list.keys():
        print(title_text, subdiv)
        for sec in subdiv_list[subdiv]:
            print("", sec, end=" ")
        print("")


if __name__ == "__main__":

    populate_subdivision_lists("|||")

    get_section_dict()

    print_subdivisions(subtitles, "Subtitle:")
    print_subdivisions(chapters, "Chapter:")
    print_subdivisions(subchapters, "Subchapter:")
    print_subdivisions(parts, "Part:")
    print_subdivisions(subparts, "Subpart:")

    print(status_statistics)
