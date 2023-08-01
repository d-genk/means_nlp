import os

def combine_jsonl(path_to_volume_root):
    for folder, subfolders, files in os.walk(path_to_volume_root):
        official_text = ""
        for file in files:
            if ".DS" in file:
                continue            
            with open(os.path.join(folder, file), "r", encoding="utf-8") as infile:
                for line in infile:
                    official_text += line
    
    path_components = path_to_volume_root.split("\\")
    id = path_components[len(path_components) - 1]
    
    with open(os.path.join(path_to_volume_root, id + ".jsonl"), "w", encoding="utf-8") as outfile:
        outfile.write(official_text)

combine_jsonl("C:\\Users\\genkindn\\means_nlp\\lighttag_jsonl\\750003")