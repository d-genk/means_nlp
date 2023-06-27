def transformer(path):    
    out_path = path[:path.find(".")] + ".jsonl"
    out_text = ""

    with open(path, "r") as infile:
        for line in infile:
            line = line.replace("\n", "")
            if len(line) == 0:
                continue
            #line = line[:y]  
            #print(line)        
            linea= "{\"text\": \"" + line + "\"}\n"
            out_text += linea

    with open(out_path, "w") as outfile:
        for line in out_text:
            outfile.write(line)
            
a= input("Enter your file ")
transformer(a)