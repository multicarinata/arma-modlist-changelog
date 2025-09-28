from bs4 import BeautifulSoup
import logging
import re
from tkinter import filedialog
from urllib.request import urlopen

# file dialogues for selecting new and old modlists
new_modlist_path = filedialog.askopenfile(filetypes=[("Arma 3 modlists", "*.html")], title = "Select your new modlist.").name
old_modlist_path = filedialog.askopenfile(filetypes=[("Arma 3 modlists", "*.html")], title = "Select your old modlist.").name
combined_modlists = {}

# creates text file with same name as new modlist
logging.basicConfig(filename = new_modlist_path.split(".html")[0] + "_CHANGELOG.txt",
                    encoding = "utf-8",
                    format="{message}",
                    style="{",
                    level = logging.INFO)

# in case you want to copy stuff off the console instead of the text file
def note(note_string):
    print(str(note_string))
    logging.info(str(note_string))

# extracts list of mods from default a3 modlist formatting
def extract_modlist(html_file):
    with open(html_file, 'r', encoding="utf-8") as file:
        
        file_text = file.read()
        header_text = file_text.split("<style>")[0]

        # extracts modlist name from html
        modlist_title = str(header_text
                            .split('''name="arma:PresetName" content="''')[1]
                            .split('"')[0])
        modlist_text = file_text.split('''<div class="mod-list">''')[1]
        modlist_dict = {}
        modlist_size = 0.0

        # extracts each mod's display (steam) name and URL
        for split_file in modlist_text.split('''data-type="DisplayName">''')[1:]:

            displayname = re.sub(r"  ",
                                 " ",
                                 split_file.split("</td>")[0])
            
            displayname = re.sub(r"&amp",
                                 "&",
                                 displayname)
            
            displayname = re.sub('''[\\?/*\\[\\]\\(\\)\\.\\;\\,\\|]''' ,
                                 '',
                                 displayname)
            
            mod_url_startpos = split_file.find('''data-type="Link">''')
            mod_url_endpos = split_file.find("</a>")
            mod_url = re.sub('''data-type="Link">''',
                             "",
                             split_file[mod_url_startpos:mod_url_endpos])

            # checks if mod size has not already been pulled
            if mod_url not in combined_modlists:
                steam_page = str(BeautifulSoup(urlopen(mod_url),features="html.parser"))
                mod_size_string = steam_page.split('''<div class="detailsStatsContainerRight">''')[1].split('''StatRight">''')[1].split('''</div''')[0]
                
                # pulls size and adjusts based on suffix
                suffix_dict = {" GB" : 0,
                               " MB" : -1,
                               " KB" : -2,
                                " B" : -3}
                for suffix in suffix_dict:
                    if str(suffix) in mod_size_string:
                        mod_size = float(mod_size_string[:len(suffix)])*(1024**suffix_dict[suffix])
                combined_modlists.update({mod_url:mod_size})
            
            # if mod size has already been pulled, no need to scrape page
            else:
                mod_size = combined_modlists[mod_url]
            modlist_dict.update({mod_url:[displayname,mod_size]})
            modlist_size += mod_size

        modlist_formatted = [modlist_title,modlist_dict,modlist_size]
        return modlist_formatted
    
new_modlist = extract_modlist(new_modlist_path)
new_modlist_title = str(new_modlist[0])
new_modlist_dict = dict(new_modlist[1])
new_modlist_size = new_modlist[2]

old_modlist = extract_modlist(old_modlist_path)
old_modlist_title = str(old_modlist[0])
old_modlist_dict = dict(old_modlist[1])
old_modlist_size = old_modlist[2]

update_size = round(new_modlist_size - old_modlist_size,1)

def format_changelist(given_dict, compare_dict, add_link):
    formatted_list = []
    change_size = 0.0

    for given_key in given_dict:
        if given_key not in compare_dict:
            display_string = str(given_dict[given_key][0])
            if add_link == True:
                formatted_list.append("- [" + display_string + "](<" + str(given_key) + ">)")
            else:
                formatted_list.append("- " + display_string)
            change_size+=float(given_dict[given_key][1])

    changelist = [formatted_list,change_size]
    return changelist

add_list_tuple = format_changelist(new_modlist_dict, old_modlist_dict, True)
modlist_add_list = add_list_tuple[0]
modlist_add_size = add_list_tuple[1]

remove_list_tuple = format_changelist(old_modlist_dict, new_modlist_dict, False)
modlist_remove_list = remove_list_tuple[0]
modlist_remove_size = remove_list_tuple[1]

note("---CHANGELOG MESSAGE STARTS BELOW---" +
     "\n## "+ new_modlist_title +
     "\nTotal mods: **" + str(len(new_modlist_dict)) + "**")

if round(modlist_add_size,0) > 0:
    download_size_string = "Download size: **" + str(round(modlist_add_size)) + " GB**"
elif round(modlist_add_size,2) > 0:
    download_size_string = "Download size: **" + str(round(1024*modlist_add_size)) + " MB**"
else:
    download_size_string = "Download size: **<10 MB**"

note(download_size_string)

# check if there have actually been changes
if len(modlist_add_list) > 0 or len(modlist_remove_list) > 0:
    note("Changes from " + old_modlist_title + ":")
    if len(modlist_add_list) > 0:
        note("### Add " + str(len(modlist_add_list)) + ":")
        for entry in sorted(modlist_add_list):
            note(entry)
    if len(modlist_remove_list) > 0:
        note("### Remove " + str(len(modlist_remove_list)) + ":")
        for entry in sorted(modlist_remove_list):
            note(entry)
else:
    note("No changes from " + old_modlist_title)

note("Total modlist size: " + str(new_modlist_size) + " GB")

# only announces change in size if the magnitude of the change is > 1GB
if round(new_modlist_size - old_modlist_size,0) > 0:
    note("New modlist is " + str(update_size) + " GB larger than " + old_modlist_title)
elif round(new_modlist_size - old_modlist_size,0) < 0:
    note("New modlist is " + str(-1*update_size) + " GB smaller than " + old_modlist_title)

note("---END CHANGELOG MESSAGE. ANNOUNCEMENT MESSAGE STARTS BELOW---" +
     "\n## " + new_modlist_title +
     "\n" + download_size_string)