import json

with open('annotations_annotations.json') as infile:    
    annotation = json.load(infile)

ordered_annotation = []

with open('full_transcription.jsonl') as infile:
    for line in infile:
        text = line[10:line.find('}') - 1]
        ordered_annotation.append({'text': text})
        ordered_annotation[len(ordered_annotation) - 1]['annotations'] = []
        for ann_line in annotation['examples']:
            if text == ann_line['content'] and 'annotations' in ann_line:
                for annot in ann_line['annotations']:
                    ordered_annotation[len(ordered_annotation) - 1]['annotations'].append(annot)

annotation_dict_list = []

for line in ordered_annotation:
    for annotation in line['annotations']:
        annotation_dict_list.append({'text': line['text']})
        annotation_dict_list[len(annotation_dict_list) - 1]['entity'] = annotation['value']
        annotation_dict_list[len(annotation_dict_list) - 1]['start'] = annotation['start']
        annotation_dict_list[len(annotation_dict_list) - 1]['end'] = annotation['end']
        annotation_dict_list[len(annotation_dict_list) - 1]['label'] = annotation['tag']

print(annotation_dict_list[:3])



