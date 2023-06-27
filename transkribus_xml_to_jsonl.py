def transformer(path):
    import os    
    out_path = path[:path.find(".")] + ".jsonl"
    out_text = ""
    target_string = "                <TextEquiv>"
    next_line_needed = False

    for folder, subfolders, files in os.walk(path):
        for file in files:            
            if not "xml" in file:
                continue
            
            with open(os.path.join(folder, file), "r") as infile:
                for line in infile:
                    if next_line_needed:
                        line = line[line.find('>') + 1:line.find('<', line.find('<') + 1)]
                        line = "{\"text\": \"" + line + "\"}\n"                                 
                        out_text += line
                        next_line_needed = False
                    if line[0:len(target_string)] == target_string:
                        next_line_needed = True

    with open(out_path, "w") as outfile:
        for line in out_text:
            outfile.write(line)
            
a= input("Enter the folder containing the XML transcriptions: ")
transformer(a)