from bs4 import BeautifulSoup
import re
from tkinter import filedialog
from urllib.request import urlopen

new_modlist_path = filedialog.askopenfile(filetypes=[("Arma 3 modlists", "*.html")], title = "Select your new modlist.").name
old_modlist_path = filedialog.askopenfile(filetypes=[("Arma 3 modlists", "*.html")], title = "Select your old modlist.").name

combined_modlists = {}

def extract_modlist(html_file):
    with open(html_file, 'r', encoding="utf-8") as file:

        file_text = file.read()
        header_text = file_text.split("<style>")[0]
        modlist_title = str(header_text.split('''name="arma:PresetName" content="''')[1].split('"')[0])
        modlist_text = file_text.split('''<div class="mod-list">''')[1]
        modlist_dict = {}
        modlist_size = 0.0

        for split_file in modlist_text.split('''data-type="DisplayName">''')[1:]:

            displayname = re.sub(r"  ", " ", split_file.split("</td>")[0])
            displayname = re.sub(r"&amp", "&", displayname)
            displayname = re.sub('''[\\?/*\\[\\]\\(\\)\\.\\;\\,\\|]''' , '', displayname)
            mod_url_startpos = split_file.find('''data-type="Link">''')
            mod_url_endpos = split_file.find("</a>")
            mod_url = re.sub('''data-type="Link">''', "", split_file[mod_url_startpos:mod_url_endpos])

            if mod_url not in combined_modlists:
                steam_page = str(BeautifulSoup(urlopen(mod_url),features="html.parser"))
                mod_size = steam_page.split('''<div class="detailsStatsContainerRight">''')[1].split('''StatRight">''')[1].split('''</div''')[0]
                
                if "KB" in mod_size:
                    size_multiplier = 0.000001
                elif "MB" in mod_size:
                    size_multiplier = 0.001
                elif "GB" in mod_size:
                    size_multiplier = 1.0
                elif " B" in mod_size:
                    size_multiplier = 0
                else:
                    print(mod_url + ": size calc error: " + mod_size)
                    size_multiplier = 1.0
                
                mod_size = float(mod_size[:-3])*size_multiplier
                combined_modlists.update({mod_url:mod_size})
            else:
                mod_size = combined_modlists[mod_url]
            modlist_dict.update({mod_url:[displayname,mod_size]})
            modlist_size += mod_size

        modlist_formatted = [modlist_title,modlist_dict,modlist_size]
        return modlist_formatted
    
new_modlist = extract_modlist(new_modlist_path)
new_modlist_title = new_modlist[0]
new_modlist_dict = dict(new_modlist[1])
new_modlist_size = round(new_modlist[2],1)
old_modlist = extract_modlist(old_modlist_path)
old_modlist_title = old_modlist[0]
old_modlist_dict = dict(old_modlist[1])
old_modlist_size = round(old_modlist[2],1)
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

modlist_add_list = format_changelist(new_modlist_dict, old_modlist_dict, True)[0]
modlist_add_size = format_changelist(new_modlist_dict, old_modlist_dict, True)[1]
modlist_remove_list = format_changelist(old_modlist_dict, new_modlist_dict, False)[0]
modlist_remove_size = format_changelist(old_modlist_dict, new_modlist_dict, False)[1]

print("---CHANGELOG MESSAGE STARTS BELOW---")
print("## " + new_modlist_title)
print("Total mods: **" + str(len(new_modlist_dict)) + "**")
print("Download size: **" + str(round(modlist_add_size,1)) + " GB**")

if len(modlist_add_list) > 0 or len(modlist_remove_list) > 0:
    print("Changes from " + str(old_modlist_title) + ":")
    if len(modlist_add_list) > 0:
        print("### Add " + str(len(modlist_add_list)) + ":")
        for entry in sorted(modlist_add_list):
            print(entry)
    if len(modlist_remove_list) > 0:
        print("### Remove " + str(len(modlist_remove_list)) + ":")
        for entry in sorted(modlist_remove_list):
            print(entry)
else:
    print("No changes from " + str(old_modlist_title))

print("Total modlist size: " + str(new_modlist_size) + " GB")

if round(new_modlist_size - old_modlist_size,1) > 0:
    print("New modlist is " + str(update_size) + " GB larger than " + old_modlist_title)
elif round(new_modlist_size - old_modlist_size,1) < 0:
    print("New modlist is " + str(-1*update_size) + " GB smaller than " + old_modlist_title)

print("---END CHANGELOG MESSAGE. ANNOUNCEMENT MESSAGE STARTS BELOW---")
print("## " + new_modlist_title)
print("Download size: " + str(round(modlist_add_size,1)) + " GB")