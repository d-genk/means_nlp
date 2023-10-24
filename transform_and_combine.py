import os

def combine_jsonl(path_to_volume_root):
    for folder, subfolders, files in os.walk(path_to_volume_root):
        official_text = ""
        for file in files:
            if ".DS" in file:
                continue     
            out_path = file[:file.find(".")] + ".jsonl"           

            with open(os.path.join(folder, file), "r", encoding="utf-8") as infile:
                for line in infile:
                    while line[0]== " ":
                        line = line [1:]
                    if line[0] == "<":
                        continue
                    line = line.replace("\n", "")
                    line = line.replace("\"", "")
                    if len(line) == 0:
                        continue      
                            
                    linea= "{\"text\": \"" + line + "\"}\n"
                    official_text += linea            
    
    path_components = path_to_volume_root.split("\\")
    id = path_components[len(path_components) - 1]
    
    with open(os.path.join(path_to_volume_root, id + ".jsonl"), "w", encoding="utf-8") as outfile:
        outfile.write(official_text)

path = input("Enter a path: ")
combine_jsonl(path)